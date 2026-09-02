@0x8b3c2f1a9e4d7c60;

struct LogMetadata {
  status @0 :UInt16;
  durationMs @1 :UInt32;
  bytesSent @2 :UInt32;
  userAgent @3 :Text;
  remoteAddr @4 :Text;
}

struct LogEntry {
  timestamp @0 :Text;
  level @1 :Text;
  message @2 :Text;
  requestId @3 :Text;
  metadata @4 :LogMetadata;
}

struct LogDataset {
  version @0 :UInt32;
  domain @1 :Text;
  tier @2 :Text;
  entries @3 :List(LogEntry);
}
