#include <vector>

#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/scheduler.h"
#include "dram_controller/rowpolicy.h"

namespace Ramulator {

class OpenRowPolicy : public IRowPolicy, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IRowPolicy, OpenRowPolicy, "OpenRowPolicy", "Open Row Policy.")
  private:
    
  public:
    void init() override { };

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override { };

    void update(bool request_found, ReqBuffer::iterator& req_it) override { 
      // OpenRowPolicy does not need to take any actions
    };


};

class ClosedRowPolicy : public IRowPolicy, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IRowPolicy, ClosedRowPolicy, "ClosedRowPolicy", "Close Row Policy.")
  private:
    IDRAM* m_dram;

    int m_PRE_req_id = -1;

    int m_RD_id  = -1;
    int m_WR_id  = -1;
    int m_RDA_id = -1;
    int m_WRA_id = -1;
    bool m_auto_precharge_available = false;

    int m_cap = -1;

    int m_rank_level = -1;
    int m_bankgroup_level = -1;
    int m_bank_level = -1;
    int m_row_level = -1;
    int m_num_ranks = -1;
    int m_num_bankgroups = -1;
    int m_num_banks = -1;

    int s_num_close_reqs = 0;
    int s_num_auto_precharge_reqs = 0;
    int s_num_priority_pre_reqs = 0;

    std::vector<uint64_t> m_col_accesses;

  public:
    void init() override { };

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
      m_ctrl = cast_parent<IDRAMController>();
      m_dram = m_ctrl->m_dram;

      m_cap = param<int>("cap").default_val(1); // Strict Closed-Row Policy by default (close after every access)

      m_rank_level = m_dram->m_levels("rank");
      m_bankgroup_level = m_dram->m_levels("bankgroup");
      m_bank_level = m_dram->m_levels("bank");
      m_row_level = m_dram->m_levels("row");

      m_PRE_req_id = m_dram->m_requests("close-row");

      m_RD_id  = m_dram->m_commands("RD");
      m_WR_id  = m_dram->m_commands("WR");
      m_RDA_id = m_dram->m_commands("RDA");
      m_WRA_id = m_dram->m_commands("WRA");
      m_auto_precharge_available = (m_RDA_id != -1) && (m_WRA_id != -1);

      m_num_ranks = m_dram->get_level_size("rank");
      m_num_bankgroups = m_dram->get_level_size("bankgroup");
      m_num_banks = m_dram->get_level_size("bank");

      m_col_accesses.resize(m_num_banks * m_num_bankgroups * m_num_ranks, 0);

      register_stat(s_num_close_reqs).name("num_close_reqs");
      register_stat(s_num_auto_precharge_reqs).name("num_auto_precharge_reqs");
      register_stat(s_num_priority_pre_reqs).name("num_priority_pre_reqs");
    };

    void update(bool request_found, ReqBuffer::iterator& req_it) override {

      if (!request_found)
        return;

      if (m_dram->m_command_meta(req_it->command).is_closing ||
          m_dram->m_command_meta(req_it->command).is_refreshing)  // PRE or REF
      {

        if (req_it->addr_vec[m_bankgroup_level] == -1 && req_it->addr_vec[m_bank_level] == -1) {  // all bank closes
          for (int b = 0; b < m_num_banks; b++) {
            for (int bg = 0; bg < m_num_bankgroups; bg++) {
              int rank_id = req_it->addr_vec[m_rank_level];
              int flat_bank_id = b + bg * m_num_banks + rank_id * m_num_banks * m_num_bankgroups;
              m_col_accesses[flat_bank_id] = 0;
            }
          }
        } else if (req_it->addr_vec[m_bankgroup_level] == -1) {  // same bank closes
          for (int bg = 0; bg < m_num_bankgroups; bg++) {
            int bank_id = req_it->addr_vec[m_bank_level];
            int rank_id = req_it->addr_vec[m_rank_level];
            int flat_bank_id = bank_id + bg * m_num_banks + rank_id * m_num_banks * m_num_bankgroups;
            m_col_accesses[flat_bank_id] = 0;
          }
        } else {  // single bank closes  (PRE, VRR, RDA, WRA)
          int flat_bank_id = req_it->addr_vec[m_bank_level] + 
                             req_it->addr_vec[m_bankgroup_level] * m_num_banks + 
                             req_it->addr_vec[m_rank_level] * m_num_banks * m_num_bankgroups;

          m_col_accesses[flat_bank_id] = 0;
        }
      } else if (m_dram->m_command_meta(req_it->command).is_accessing)  // RD or WR
      {
        int flat_bank_id = req_it->addr_vec[m_bank_level] + 
                           req_it->addr_vec[m_bankgroup_level] * m_num_banks + 
                           req_it->addr_vec[m_rank_level] * m_num_banks * m_num_bankgroups;
        
        m_col_accesses[flat_bank_id]++;

        if (m_col_accesses[flat_bank_id] >= m_cap) {
          if (m_auto_precharge_available &&
              (req_it->command == m_RD_id || req_it->command == m_WR_id)) {
            if (req_it->command == m_RD_id) {
              req_it->command = m_RDA_id;
              req_it->final_command = m_RDA_id;
            } else {
              req_it->command = m_WRA_id;
              req_it->final_command = m_WRA_id;
            }
            m_col_accesses[flat_bank_id] = 0;
            s_num_close_reqs++;
            s_num_auto_precharge_reqs++;
          } else {
            Request req(req_it->addr_vec, m_PRE_req_id);
            m_ctrl->priority_send(req);
            m_col_accesses[flat_bank_id] = 0;
            s_num_close_reqs++;
            s_num_priority_pre_reqs++;
          }
        }
      }
    };
};


class ClosedWithAutoPrecharge : public IRowPolicy, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IRowPolicy, ClosedWithAutoPrecharge,
      "ClosedWithAutoPrecharge",
      "Closed Row Policy with Auto-Precharge (RDA/WRA).")
  private:
    IDRAM* m_dram;

    int m_RD_id  = -1;   // m_dram->m_commands("RD")
    int m_WR_id  = -1;   // m_dram->m_commands("WR")
    int m_RDA_id = -1;   // m_dram->m_commands("RDA")
    int m_WRA_id = -1;   // m_dram->m_commands("WRA")

  public:
    void init() override { }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
      m_ctrl = cast_parent<IDRAMController>();
      m_dram = m_ctrl->m_dram;

      m_RD_id  = m_dram->m_commands("RD");
      m_WR_id  = m_dram->m_commands("WR");
      m_RDA_id = m_dram->m_commands("RDA");
      m_WRA_id = m_dram->m_commands("WRA");
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
      if (!request_found)
        return;

      if (req_it->command == m_RD_id) {
        req_it->command = m_RDA_id;
        req_it->final_command = m_RDA_id;
      } else if (req_it->command == m_WR_id) {
        req_it->command = m_WRA_id;
        req_it->final_command = m_WRA_id;
      }
    }
};


}       // namespace Ramulator
