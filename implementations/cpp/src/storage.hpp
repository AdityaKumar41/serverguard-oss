#pragma once

#include <string>
#include <vector>

#include "event.hpp"

namespace sg {

class EventStore {
 public:
  explicit EventStore(std::string data_dir);
  ~EventStore();

  EventStore(const EventStore&) = delete;
  EventStore& operator=(const EventStore&) = delete;

  void insert(const Event& event);
  std::vector<Event> list_events() const;

 private:
  void* db_ = nullptr;
};

}  // namespace sg

