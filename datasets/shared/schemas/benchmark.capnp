@0xf4a8c2e19b3d7051;

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

struct ProfilePreferences {
  locale @0 :Text;
  newsletter @1 :Bool;
  theme @2 :Text;
}

struct ProfileAddress {
  city @0 :Text;
  postalCode @1 :Text;
  country @2 :Text;
}

struct Profile {
  id @0 :Text;
  name @1 :Text;
  email @2 :Text;
  active @3 :Bool;
  tags @4 :List(Text);
  preferences @5 :ProfilePreferences;
  address @6 :ProfileAddress;
}

struct ProfileDataset {
  version @0 :UInt32;
  domain @1 :Text;
  tier @2 :Text;
  profiles @3 :List(Profile);
}

struct Vertex {
  x @0 :Float32;
  y @1 :Float32;
  z @2 :Float32;
  nx @3 :Float32;
  ny @4 :Float32;
  nz @5 :Float32;
}

struct MeshDataset {
  version @0 :UInt32;
  domain @1 :Text;
  tier @2 :Text;
  name @3 :Text;
  vertices @4 :List(Vertex);
  indices @5 :List(UInt32);
}

struct KeyValue {
  key @0 :Text;
  value @1 :Text;
}

struct Product {
  sku @0 :Text;
  name @1 :Text;
  priceCents @2 :UInt32;
  currency @3 :Text;
  inStock @4 :Bool;
  tags @5 :List(Text);
  attributes @6 :List(KeyValue);
}

struct CatalogDataset {
  version @0 :UInt32;
  domain @1 :Text;
  tier @2 :Text;
  products @3 :List(Product);
}
