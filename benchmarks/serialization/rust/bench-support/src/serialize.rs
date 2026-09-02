use crate::dataset::Dataset;

#[cfg(feature = "simd-json")]
pub fn simd_json(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => simd_json::serde::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => simd_json::serde::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => simd_json::serde::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => simd_json::serde::to_vec(value).expect("serialize output"),
    }
}

pub fn json(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => serde_json::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => serde_json::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => serde_json::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => serde_json::to_vec(value).expect("serialize output"),
    }
}

#[cfg(feature = "bitcode")]
pub fn bitcode(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => ::bitcode::encode(value),
        Dataset::Profile(value) => ::bitcode::encode(value),
        Dataset::Mesh(value) => ::bitcode::encode(value),
        Dataset::Catalog(value) => ::bitcode::encode(value),
    }
}

#[cfg(feature = "rkyv")]
pub fn rkyv(data: &Dataset) -> Vec<u8> {
    use rkyv::{rancor::Error, to_bytes};

    match data {
        Dataset::Logs(value) => to_bytes::<Error>(value)
            .expect("serialize output")
            .into_vec(),
        Dataset::Profile(value) => to_bytes::<Error>(value)
            .expect("serialize output")
            .into_vec(),
        Dataset::Mesh(value) => to_bytes::<Error>(value)
            .expect("serialize output")
            .into_vec(),
        Dataset::Catalog(value) => to_bytes::<Error>(value)
            .expect("serialize output")
            .into_vec(),
    }
}

#[cfg(feature = "flexbuffers")]
pub fn flexbuffers(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => flexbuffers::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => flexbuffers::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => flexbuffers::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => flexbuffers::to_vec(value).expect("serialize output"),
    }
}

#[cfg(feature = "rmp-serde")]
pub fn rmp_serde(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => rmp_serde::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => rmp_serde::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => rmp_serde::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => rmp_serde::to_vec(value).expect("serialize output"),
    }
}

#[cfg(feature = "yaml")]
pub fn yaml(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => serde_yaml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Profile(value) => serde_yaml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Mesh(value) => serde_yaml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Catalog(value) => serde_yaml::to_string(value).expect("serialize output").into_bytes(),
    }
}

#[cfg(feature = "toml")]
pub fn toml_format(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => toml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Profile(value) => toml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Mesh(value) => toml::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Catalog(value) => toml::to_string(value).expect("serialize output").into_bytes(),
    }
}

#[cfg(feature = "xml")]
pub fn xml(data: &Dataset) -> Vec<u8> {
    crate::text_xml::encode(data)
}

#[cfg(feature = "ini")]
pub fn ini(data: &Dataset) -> Vec<u8> {
    crate::text_ini::encode(data)
}

#[cfg(feature = "kdl")]
pub fn kdl(data: &Dataset) -> Vec<u8> {
    crate::text_kdl::encode(data)
}

#[cfg(feature = "bson")]
pub fn bson(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => ::bson::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => ::bson::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => ::bson::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => ::bson::to_vec(value).expect("serialize output"),
    }
}

#[cfg(feature = "cbor")]
pub fn cbor(data: &Dataset) -> Vec<u8> {
    use ciborium::into_writer;
    match data {
        Dataset::Logs(value) => {
            let mut buffer = Vec::new();
            into_writer(value, &mut buffer).expect("serialize output");
            buffer
        }
        Dataset::Profile(value) => {
            let mut buffer = Vec::new();
            into_writer(value, &mut buffer).expect("serialize output");
            buffer
        }
        Dataset::Mesh(value) => {
            let mut buffer = Vec::new();
            into_writer(value, &mut buffer).expect("serialize output");
            buffer
        }
        Dataset::Catalog(value) => {
            let mut buffer = Vec::new();
            into_writer(value, &mut buffer).expect("serialize output");
            buffer
        }
    }
}

#[cfg(feature = "csv")]
pub fn csv(data: &Dataset) -> Vec<u8> {
    crate::text_csv::encode(data, crate::text_csv::Delimiter::Comma)
}

#[cfg(feature = "tsv")]
pub fn tsv(data: &Dataset) -> Vec<u8> {
    crate::text_csv::encode(data, crate::text_csv::Delimiter::Tab)
}

#[cfg(feature = "json5")]
pub fn json5_format(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => ::json5::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Profile(value) => ::json5::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Mesh(value) => ::json5::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Catalog(value) => ::json5::to_string(value).expect("serialize output").into_bytes(),
    }
}

#[cfg(feature = "hjson")]
pub fn hjson_format(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => ::serde_hjson::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Profile(value) => ::serde_hjson::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Mesh(value) => ::serde_hjson::to_string(value).expect("serialize output").into_bytes(),
        Dataset::Catalog(value) => ::serde_hjson::to_string(value).expect("serialize output").into_bytes(),
    }
}

#[cfg(feature = "cjson")]
pub fn cjson(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => sonic_rs::to_vec(value).expect("serialize output"),
        Dataset::Profile(value) => sonic_rs::to_vec(value).expect("serialize output"),
        Dataset::Mesh(value) => sonic_rs::to_vec(value).expect("serialize output"),
        Dataset::Catalog(value) => sonic_rs::to_vec(value).expect("serialize output"),
    }
}

#[cfg(feature = "plist")]
pub fn plist_format(data: &Dataset) -> Vec<u8> {
    let mut buffer = Vec::new();
    match data {
        Dataset::Logs(value) => ::plist::to_writer_xml(&mut buffer, value).expect("serialize output"),
        Dataset::Profile(value) => ::plist::to_writer_xml(&mut buffer, value).expect("serialize output"),
        Dataset::Mesh(value) => ::plist::to_writer_xml(&mut buffer, value).expect("serialize output"),
        Dataset::Catalog(value) => ::plist::to_writer_xml(&mut buffer, value).expect("serialize output"),
    }
    buffer
}

#[cfg(feature = "ucl")]
pub fn ucl(data: &Dataset) -> Vec<u8> {
    crate::text_ucl::encode(data)
}
