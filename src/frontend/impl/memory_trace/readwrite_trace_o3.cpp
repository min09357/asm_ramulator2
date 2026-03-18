#include <filesystem>
#include <iostream>
#include <fstream>

#include "frontend/frontend.h"
#include "base/exception.h"

namespace Ramulator {

namespace fs = std::filesystem;

class ReadWriteTraceO3 : public IFrontEnd, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IFrontEnd, ReadWriteTraceO3, "ReadWriteTraceO3", "Read/Write DRAM address vector trace with out-of-order issue window.")

  private:
    struct Trace {
      bool is_write;
      AddrVec_t addr_vec;
    };
    std::vector<Trace> m_trace;
    std::vector<bool> m_sent;

    size_t m_trace_length = 0;
    size_t m_head = 0;             // Window start (oldest unsent entry)
    size_t m_trace_count = 0;
    int m_issue_window_size = 64;

    Logger_t m_logger;

  public:
    void init() override {
      std::string trace_path_str = param<std::string>("path").desc("Path to the load store trace file.").required();
      m_clock_ratio = param<uint>("clock_ratio").required();
      m_issue_window_size = param<int>("issue_window_size").desc("Out-of-order issue window size.").default_val(64);

      m_logger = Logging::create_logger("ReadWriteTraceO3");
      m_logger->info("Loading trace file {} ...", trace_path_str);
      init_trace(trace_path_str);
      m_logger->info("Loaded {} lines. Issue window size: {}", m_trace.size(), m_issue_window_size);
    };


    void tick() override {
      size_t window_end = std::min(m_head + (size_t)m_issue_window_size, m_trace_length);
      for (size_t i = m_head; i < window_end; i++) {
        if (m_sent[i]) continue;

        const Trace& t = m_trace[i];
        bool request_sent = m_memory_system->send({t.addr_vec, t.is_write ? Request::Type::Write : Request::Type::Read});
        if (request_sent) {
          m_sent[i] = true;
          m_trace_count++;
          break;
        }
      }
      // Advance head past contiguous sent entries
      while (m_head < m_trace_length && m_sent[m_head]) {
        m_head++;
      }
    };


  private:
    void init_trace(const std::string& file_path_str) {
      fs::path trace_path(file_path_str);
      if (!fs::exists(trace_path)) {
        throw ConfigurationError("Trace {} does not exist!", file_path_str);
      }

      std::ifstream trace_file(trace_path);
      if (!trace_file.is_open()) {
        throw ConfigurationError("Trace {} cannot be opened!", file_path_str);
      }

      std::string line;
      while (std::getline(trace_file, line)) {
        std::vector<std::string> tokens;
        tokenize(tokens, line, " ");

        if (tokens.size() != 2) {
          throw ConfigurationError("Trace {} format invalid!", file_path_str);
        }

        bool is_write = false;
        if (tokens[0] == "R") {
          is_write = false;
        } else if (tokens[0] == "W") {
          is_write = true;
        } else {
          throw ConfigurationError("Trace {} format invalid!", file_path_str);
        }

        std::vector<std::string> addr_vec_tokens;
        tokenize(addr_vec_tokens, tokens[1], ",");

        AddrVec_t addr_vec;
        for (const auto& token : addr_vec_tokens) {
          addr_vec.push_back(std::stoll(token));
        }

        m_trace.push_back({is_write, addr_vec});
      }

      trace_file.close();

      m_trace_length = m_trace.size();
      m_sent.resize(m_trace_length, false);
    };

    bool is_finished() override {
      return m_trace_count >= m_trace_length;
    };
};

}        // namespace Ramulator
