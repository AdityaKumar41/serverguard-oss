#include "storage.hpp"
#include <dlfcn.h>
#include <filesystem>
#include <stdexcept>

namespace sg {
namespace {
using sqlite3 = void;
using sqlite3_stmt = void;
constexpr int SQLITE_OK = 0, SQLITE_ROW = 100, SQLITE_DONE = 101;
using Destructor = void (*)(void*);
const Destructor SQLITE_TRANSIENT = reinterpret_cast<Destructor>(-1);

template <typename T>
T sym(void* lib, const char* name) {
  auto* value = dlsym(lib, name);
  if (!value) throw std::runtime_error(std::string("missing sqlite symbol: ") + name);
  return reinterpret_cast<T>(value);
}
struct Api {
  void* lib = dlopen("libsqlite3.so.0", RTLD_LAZY);
  int (*open)(const char*, sqlite3**) = sym<decltype(open)>(lib, "sqlite3_open");
  int (*close)(sqlite3*) = sym<decltype(close)>(lib, "sqlite3_close");
  int (*exec)(sqlite3*, const char*, void*, void*, char**) =
      sym<decltype(exec)>(lib, "sqlite3_exec");
  int (*prepare)(sqlite3*, const char*, int, sqlite3_stmt**, const char**) =
      sym<decltype(prepare)>(lib, "sqlite3_prepare_v2");
  int (*step)(sqlite3_stmt*) = sym<decltype(step)>(lib, "sqlite3_step");
  int (*finalize)(sqlite3_stmt*) = sym<decltype(finalize)>(lib, "sqlite3_finalize");
  int (*bind_text)(sqlite3_stmt*, int, const char*, int, Destructor) =
      sym<decltype(bind_text)>(lib, "sqlite3_bind_text");
  const unsigned char* (*column_text)(sqlite3_stmt*, int) =
      sym<decltype(column_text)>(lib, "sqlite3_column_text");
};
Api& api() {
  static Api value;
  if (!value.lib) throw std::runtime_error("could not load libsqlite3.so.0");
  return value;
}
void exec_sql(sqlite3* db, const char* sql) {
  if (api().exec(db, sql, nullptr, nullptr, nullptr) != SQLITE_OK) {
    throw std::runtime_error("sqlite exec failed");
  }
}
std::string text(sqlite3_stmt* stmt, int column) {
  const auto* raw = api().column_text(stmt, column);
  return raw ? reinterpret_cast<const char*>(raw) : "";
}
}  // namespace
EventStore::EventStore(std::string data_dir) {
  std::filesystem::create_directories(data_dir);
  auto path = std::filesystem::path(data_dir) / "serverguard.db";
  if (api().open(path.string().c_str(), reinterpret_cast<sqlite3**>(&db_)) != SQLITE_OK) {
    throw std::runtime_error("database open failure");
  }
  exec_sql(static_cast<sqlite3*>(db_),
           "CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY,timestamp TEXT NOT "
           "NULL,type TEXT NOT NULL,severity TEXT NOT NULL,source TEXT NOT NULL,subject "
           "TEXT NOT NULL,message TEXT NOT NULL,metadata_json TEXT NOT NULL);"
           "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);"
           "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);"
           "CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject);");
}

EventStore::~EventStore() { if (db_) api().close(static_cast<sqlite3*>(db_)); }

void EventStore::insert(const Event& event) {
  sqlite3_stmt* stmt = nullptr;
  const char* sql = "INSERT INTO events VALUES (?,?,?,?,?,?,?,?)";
  if (api().prepare(static_cast<sqlite3*>(db_), sql, -1, &stmt, nullptr) != SQLITE_OK)
    throw std::runtime_error("event insert prepare failed");
  const std::string values[] = {event.id,     event.timestamp, event.type,    event.severity,
                                event.source, event.subject,   event.message, event.metadata_json};
  for (int i = 0; i < 8; ++i) {
    api().bind_text(stmt, i + 1, values[i].c_str(), -1, SQLITE_TRANSIENT);
  }
  if (api().step(stmt) != SQLITE_DONE) throw std::runtime_error("event insert failed");
  api().finalize(stmt);
}

std::vector<Event> EventStore::list_events() const {
  sqlite3_stmt* stmt = nullptr;
  const char* sql = "SELECT id,timestamp,type,severity,source,subject,message,metadata_json "
                    "FROM events ORDER BY timestamp DESC,id DESC";
  if (api().prepare(static_cast<sqlite3*>(db_), sql, -1, &stmt, nullptr) != SQLITE_OK)
    throw std::runtime_error("event list prepare failed");
  std::vector<Event> events;
  while (api().step(stmt) == SQLITE_ROW) {
    events.push_back({text(stmt, 0), text(stmt, 1), text(stmt, 2), text(stmt, 3),
                      text(stmt, 4), text(stmt, 5), text(stmt, 6), text(stmt, 7)});
  }
  api().finalize(stmt);
  return events;
}

}  // namespace sg
