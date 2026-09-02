use crate::catalog::CatalogDataset;
use crate::catalog;
use crate::logs::LogDataset;
use crate::logs;
use crate::mesh::MeshDataset;
use crate::mesh;
use crate::profile::ProfileDataset;
use crate::profile;
use crate::shared::domain_from_spec;

#[derive(Debug, Clone)]
pub enum Dataset {
    Logs(LogDataset),
    Profile(ProfileDataset),
    Mesh(MeshDataset),
    Catalog(CatalogDataset),
}

pub fn load(spec: &str) -> Dataset {
    match domain_from_spec(spec) {
        "logs" => Dataset::Logs(logs::load(spec)),
        "profile" => Dataset::Profile(profile::load(spec)),
        "mesh" => Dataset::Mesh(mesh::load(spec)),
        "catalog" => Dataset::Catalog(catalog::load(spec)),
        other => panic!("unknown dataset domain: {other}"),
    }
}
