//! Differential constant-catalog evidence from a compiled PB 2022 PBL only.
//!
//! Set `PFCAPSRV_PBL` to the OpenSourcePFC 2022 `pfcapsrv.pbl` fixture. This
//! test deliberately does not open or index the matching exported source.

use adapters::pb::compiled_object::{
    CompiledConstant, CompiledConstantCatalog, CompiledConstantResolution, CompiledConstantValue,
};
use adapters::pb::object_inspector::inspect_object;
use adapters::pb::pbd_reader::PbdReader;
use std::path::Path;

fn named<'a>(constants: &'a [CompiledConstant], name: &str) -> &'a CompiledConstant {
    constants
        .iter()
        .find(|constant| constant.name.eq_ignore_ascii_case(name))
        .unwrap_or_else(|| panic!("compiled constant {name} not found"))
}

#[test]
fn recovers_strings_and_resolves_compiled_aliases_without_source() {
    let Some(path) = std::env::var_os("PFCAPSRV_PBL") else {
        eprintln!("skipped: set PFCAPSRV_PBL to run compiled-artifact evidence");
        return;
    };
    let reader = PbdReader::open(Path::new(&path)).expect("open PFCAPSRV_PBL");
    let (objects, errors) = reader.extract_objects();
    assert!(errors.is_empty(), "PBL extraction errors: {errors:?}");
    let constants = objects
        .iter()
        .flat_map(|object| inspect_object(&object.data).compiled_constants)
        .collect::<Vec<_>>();
    let catalog = CompiledConstantCatalog::from_constants(constants.clone());

    let cache_id = named(&constants, "CACHE_ID");
    let is_pfckey = named(&constants, "IS_PFCKEY");
    let database = named(&constants, "DATABASE");
    let ics_database = named(&constants, "ICS_DATABASE");

    assert!(matches!(cache_id.value, CompiledConstantValue::String(_)));
    assert!(matches!(is_pfckey.value, CompiledConstantValue::String(_)));
    assert_ne!(cache_id.value, is_pfckey.value);
    assert_eq!(database.value, ics_database.value);
    assert!(matches!(database.value, CompiledConstantValue::String(_)));

    assert!(matches!(
        catalog.resolve(&cache_id.owner_type_name, cache_id.type_ref, &cache_id.value),
        CompiledConstantResolution::Unique { candidate }
            if candidate.name.eq_ignore_ascii_case("CACHE_ID")
    ));
    assert!(matches!(
        catalog.resolve(
            &database.owner_type_name,
            database.type_ref,
            &database.value
        ),
        CompiledConstantResolution::Ambiguous { candidates }
            if candidates.len() == 2
                && candidates.iter().any(|candidate| candidate.name.eq_ignore_ascii_case("DATABASE"))
                && candidates.iter().any(|candidate| candidate.name.eq_ignore_ascii_case("ICS_DATABASE"))
    ));
    assert_eq!(
        catalog.resolve(
            &cache_id.owner_type_name,
            cache_id.type_ref,
            &CompiledConstantValue::String("not_present_in_compiled_catalog".to_string())
        ),
        CompiledConstantResolution::Zero
    );
}
