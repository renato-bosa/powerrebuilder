//! Known-source PB 2022 exception scaffolding oracles.
//!
//! The offsets and operands below are the exception-relevant subsequences from
//! OpenSourcePFC 2022 `pfcapsrv.pbl` at commit
//! 19b7ec2f8353ce9ad8fb22fd0897ef4dadb71eea. The expected catch declarations
//! come from the matching exported `pfc_n_cst_apppreference.sru`.

use adapters::pb::compiled_object::{CompiledFunctionDefinition, CompiledVariable};
use adapters::pb::pcode_scanner::{PCodeInstruction, PCodeScan};
use adapters::pb::semantic_preview::{
    build_semantic_preview, verify_known_source_constructs, verify_known_source_try_catch,
    KnownSourceCatchShape, KnownSourceFunctionOracle, KnownSourceTryCatchExpectation,
    KnownSourceTryCatchShape, VerificationStatus,
};

struct PfcExceptionOracle {
    id: &'static str,
    source_line: usize,
    setup: usize,
    first_handler: usize,
    second_handler: usize,
    end: usize,
    first_variable: u16,
    second_variable: u16,
}

const ORACLES: &[PfcExceptionOracle] = &[
    PfcExceptionOracle {
        id: "pfc_n_cst_apppreference.of_restore(integer,...)",
        source_line: 1894,
        setup: 0x0108,
        first_handler: 0x01c8,
        second_handler: 0x0218,
        end: 0x0268,
        first_variable: 13,
        second_variable: 14,
    },
    PfcExceptionOracle {
        id: "pfc_n_cst_apppreference.of_save(integer,...)",
        source_line: 1994,
        setup: 0x0106,
        first_handler: 0x01ac,
        second_handler: 0x01fc,
        end: 0x024c,
        first_variable: 12,
        second_variable: 13,
    },
    PfcExceptionOracle {
        id: "pfc_n_cst_apppreference.of_restore(string,...)",
        source_line: 2548,
        setup: 0x00d8,
        first_handler: 0x0198,
        second_handler: 0x01e8,
        end: 0x0238,
        first_variable: 11,
        second_variable: 12,
    },
];

#[test]
fn reconstructs_and_confirms_all_three_pfc_try_catch_shapes() {
    for oracle in ORACLES {
        let scan = exception_scaffold(oracle);
        let variables = exception_variables(oracle);
        let mut preview = build_semantic_preview(
            &function_definition(oracle.id),
            &variables,
            &[],
            &[],
            &[],
            &[],
            &[],
            &scan,
        );
        let expectation = KnownSourceFunctionOracle {
            oracle_id: oracle.id.to_string(),
            entry_name: "pfc_n_cst_apppreference.udo".to_string(),
            signature: preview.signature.clone(),
            source_reference: format!(
                "OpenSourcePFC-2022/ws_objects/pfcapsrv/pfcapsrv.pbl.src/\
                 pfc_n_cst_apppreference.sru:{}",
                oracle.source_line
            ),
            try_catch: vec![KnownSourceTryCatchShape {
                catches: vec![
                    KnownSourceCatchShape {
                        exception_type: "PBDOM_Exception".to_string(),
                        variable_name: "pbde".to_string(),
                    },
                    KnownSourceCatchShape {
                        exception_type: "PBXRuntimeError".to_string(),
                        variable_name: "re".to_string(),
                    },
                ],
            }],
            normalized_body_fragments: vec![
                "CATCH (PBDOM_Exception pbde) RETURN CATCH (PBXRuntimeError re) RETURN END TRY"
                    .to_string(),
            ],
        };

        assert!(
            preview.control_flow.valid,
            "{:?}",
            preview.control_flow.errors
        );
        assert_eq!(preview.control_flow.exception_regions.len(), 1);
        assert!(preview.semantically_complete, "{:?}", preview.unresolved);
        verify_known_source_constructs(&mut preview, &expectation).unwrap();

        let reconstructed = &preview.try_catch_structures[0];
        assert_eq!(reconstructed.setup_offset, oracle.setup);
        assert_eq!(reconstructed.end_offset, oracle.end);
        assert_eq!(reconstructed.catches.len(), 2);
        assert_eq!(reconstructed.catches[0].exception_type, "PBDOM_Exception");
        assert_eq!(reconstructed.catches[0].variable_name, "pbde");
        assert_eq!(reconstructed.catches[1].exception_type, "PBXRuntimeError");
        assert_eq!(reconstructed.catches[1].variable_name, "re");
        assert!(preview.powerscript_like.contains("try\n"));
        assert!(preview
            .powerscript_like
            .contains("catch (PBDOM_Exception pbde)"));
        assert!(preview
            .powerscript_like
            .contains("catch (PBXRuntimeError re)"));
        assert!(preview.powerscript_like.contains("end try"));

        assert_eq!(preview.evidence.known_source_constructs.len(), 1);
        assert_eq!(
            preview.evidence.known_source_constructs[0].compared_body_fragments,
            1
        );
        assert_eq!(
            preview.evidence.known_source_constructs[0].status,
            VerificationStatus::Verified
        );
        // Only the exception construction was compared. The full function was not.
        assert_eq!(
            preview.evidence.function_reconstruction,
            VerificationStatus::NotAssessed
        );
        assert_eq!(
            preview.evidence.object_recompilation,
            VerificationStatus::NotAssessed
        );
    }
}

#[test]
fn a_consumed_exception_shape_is_not_verified_when_the_source_oracle_differs() {
    let oracle = &ORACLES[0];
    let mut preview = build_semantic_preview(
        &function_definition(oracle.id),
        &exception_variables(oracle),
        &[],
        &[],
        &[],
        &[],
        &[],
        &exception_scaffold(oracle),
    );
    let wrong_expectation = KnownSourceTryCatchExpectation {
        oracle_id: "deliberate-mismatch".to_string(),
        source_reference: "test oracle".to_string(),
        catches: vec![("Exception".to_string(), "wrong_name".to_string())],
    };

    assert!(preview.semantically_complete);
    assert!(verify_known_source_try_catch(&mut preview, &[wrong_expectation]).is_err());
    assert_eq!(
        preview.evidence.known_source_constructs[0].status,
        VerificationStatus::Mismatch
    );
    assert_eq!(
        preview.evidence.function_reconstruction,
        VerificationStatus::NotAssessed
    );
}

fn exception_scaffold(oracle: &PfcExceptionOracle) -> PCodeScan {
    let protected_start = oracle.setup + 6;
    let first_catch = oracle.first_handler + 4;
    let first_guard = first_catch + 2;
    let first_body = first_guard + 4;
    let second_catch = oracle.second_handler + 4;
    let second_guard = second_catch + 2;
    let second_body = second_guard + 4;
    let after_end = oracle.end + 2;
    let instructions = vec![
        instruction(
            oracle.setup,
            0x01e5,
            "PUSH_TRY",
            &[oracle.first_handler as u16, oracle.end as u16],
        ),
        instruction(protected_start, 0x0000, "RETURN", &[]),
        instruction(
            oracle.first_handler,
            0x01a9,
            "PUSH_LOCAL_VAR_RP",
            &[oracle.first_variable],
        ),
        instruction(first_catch, 0x01e7, "CATCH_EXCEPTION", &[]),
        instruction(
            first_guard,
            0x0003,
            "JUMPFALSE",
            &[oracle.second_handler as u16],
        ),
        instruction(first_body, 0x0000, "RETURN", &[]),
        instruction(
            oracle.second_handler,
            0x01a9,
            "PUSH_LOCAL_VAR_RP",
            &[oracle.second_variable],
        ),
        instruction(second_catch, 0x01e7, "CATCH_EXCEPTION", &[]),
        instruction(second_guard, 0x0003, "JUMPFALSE", &[oracle.end as u16]),
        instruction(second_body, 0x0000, "RETURN", &[]),
        instruction(oracle.end, 0x01e6, "POP_TRY", &[]),
        instruction(after_end, 0x0000, "RETURN", &[]),
    ];
    PCodeScan {
        region_length: after_end + 2,
        consumed_bytes: after_end + 2,
        instruction_count: instructions.len(),
        complete: true,
        stop: None,
        instructions,
        branch_targets: Vec::new(),
    }
}

fn instruction(
    offset: usize,
    opcode: u16,
    mnemonic: &'static str,
    operands: &[u16],
) -> PCodeInstruction {
    PCodeInstruction {
        offset,
        opcode,
        mnemonic,
        operand_words: operands.len() as u8,
        operand_bytes_hex: String::new(),
        operands_u16_le: operands.to_vec(),
    }
}

fn exception_variables(oracle: &PfcExceptionOracle) -> Vec<CompiledVariable> {
    let mut variables = (0..=oracle.second_variable)
        .map(|index| variable(index, &format!("local_{index}"), "any"))
        .collect::<Vec<_>>();
    variables[oracle.first_variable as usize] =
        variable(oracle.first_variable, "pbde", "PBDOM_Exception");
    variables[oracle.second_variable as usize] =
        variable(oracle.second_variable, "re", "PBXRuntimeError");
    variables
}

fn variable(index: u16, name: &str, type_name: &str) -> CompiledVariable {
    CompiledVariable {
        index,
        name: name.to_string(),
        type_ref: 0,
        type_name: type_name.to_string(),
        array: String::new(),
        flags: 0,
        is_shared: false,
        is_referenced_global: false,
        is_instance: false,
        is_indirect: false,
        is_constant: false,
        value_or_global_index: 0,
    }
}

fn function_definition(name: &str) -> CompiledFunctionDefinition {
    CompiledFunctionDefinition {
        index: 0,
        name: name.to_string(),
        return_type_ref: 1,
        return_type_name: "integer".to_string(),
        flags: 0,
        global_index: 0,
        reference_index: 0,
        event_code: 0,
        parameters: Vec::new(),
        library: None,
        alias: None,
    }
}
