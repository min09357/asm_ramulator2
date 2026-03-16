#include "memory_system/memory_system.h"
#include "translation/translation.h"
#include "dram_controller/controller.h"
#include "addr_mapper/addr_mapper.h"
#include "dram/dram.h"

namespace Ramulator {

class GenericDRAMSystem final : public IMemorySystem, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IMemorySystem, GenericDRAMSystem, "GenericDRAM", "A generic DRAM-based memory system.");

  protected:
    Clk_t m_clk = 0;
    IDRAM*  m_dram;
    IAddrMapper*  m_addr_mapper;
    std::vector<IDRAMController*> m_controllers;

    int num_channels = 1;

  public:
    int s_num_read_requests = 0;
    int s_num_write_requests = 0;
    int s_num_other_requests = 0;

    float s_theoretical_bandwidth = 0.0f;
    float s_measured_bandwidth = 0.0f;
    float s_bandwidth_utilization = 0.0f;

  public:
    void init() override { 
      // Create device (a top-level node wrapping all channel nodes)
      m_dram = create_child_ifce<IDRAM>();
      m_addr_mapper = create_child_ifce<IAddrMapper>();

      num_channels = m_dram->get_level_size("channel");   

      // Create memory controllers
      for (int i = 0; i < num_channels; i++) {
        IDRAMController* controller = create_child_ifce<IDRAMController>();
        controller->m_impl->set_id(fmt::format("Channel {}", i));
        controller->m_channel_id = i;
        m_controllers.push_back(controller);
      }

      m_clock_ratio = param<uint>("clock_ratio").required();

      register_stat(m_clk).name("memory_system_cycles");
      register_stat(s_num_read_requests).name("total_num_read_requests");
      register_stat(s_num_write_requests).name("total_num_write_requests");
      register_stat(s_num_other_requests).name("total_num_other_requests");

      register_stat(s_theoretical_bandwidth).name("theoretical_bandwidth (GBs)");
      register_stat(s_measured_bandwidth).name("measured_bandwidth (GBs)");
      register_stat(s_bandwidth_utilization).name("bandwidth_utilization (%)");
    };

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override { }

    bool send(Request req) override {
      m_addr_mapper->apply(req);
      int channel_id = req.addr_vec[0];
      bool is_success = m_controllers[channel_id]->send(req);

      if (is_success) {
        switch (req.type_id) {
          case Request::Type::Read: {
            s_num_read_requests++;
            break;
          }
          case Request::Type::Write: {
            s_num_write_requests++;
            break;
          }
          default: {
            s_num_other_requests++;
            break;
          }
        }
      }

      return is_success;
    };
    
    void tick() override {
      m_clk++;
      m_dram->tick();
      for (auto controller : m_controllers) {
        controller->tick();
      }
    };

    float get_tCK() override {
      return m_dram->m_timing_vals("tCK_ps") / 1000.0f;
    }

    // const SpecDef& get_supported_requests() override {
    //   return m_dram->m_requests;
    // };

    void finalize() override {
      float tCK_ns        = get_tCK();
      float tCK_ps        = tCK_ns * 1000.0f;
      int   channel_width = m_dram->m_channel_width;
      int   BL            = m_dram->m_timing_vals("nBL") * 2;

      // Peak theoretical bandwidth: DDR = 2 transfers/clock
      float data_rate_MTps      = 2.0f * 1e6f / tCK_ps;
      s_theoretical_bandwidth = data_rate_MTps * num_channels * (channel_width / 8.0f) / 1000.0f;

      // Measured bandwidth: bytes/ns == GB/s
      double total_bytes        = (double)(s_num_read_requests + s_num_write_requests)
                                  * BL * (channel_width / 8.0);
      double total_time_ns      = (double)m_clk * tCK_ns;
      s_measured_bandwidth = (float)(total_bytes / total_time_ns);

      // Utilization
      s_bandwidth_utilization = (s_measured_bandwidth / s_theoretical_bandwidth) * 100.0f;

      IMemorySystem::finalize();
    }
};
  
}   // namespace 
