# PB2022 safe canonicalization and constant recoverability

## Resultado

O oracle de função inteira agora separa duas bases de verificação:

- `normalized_equality`: igualdade após a normalização superficial preexistente;
- `safe_semantic_canonicalization`: igualdade somente depois de uma regra
  sintática local cuja equivalência é preservada.

Nenhuma dessas regras altera a saída `powerscript_like`. A comparação por hash
dos 1.873 arquivos de preview entre v6 e v8 confirmou que todos permaneceram
idênticos.

| Corpus | Comparações | Igualdade normalizada | Canonicalização segura | Verified total |
|---|---:|---:|---:|---:|
| `exmmain` | 17 | 6 | 1 | 7 |
| `appexmfe` | 163 | 101 | 2 | 103 |
| `pfcapsrv` | 1.693 | 324 | 61 | 385 |
| **Total** | **1.873** | **431** | **64** | **495** |

`function_reconstruction = verified` passou de 431/1.873 (23,01%) para
495/1.873 (26,43%): ganho de 64 funções, ou 3,42 pontos percentuais. A
comparação nominal encontrou 64 promoções e zero regressões.

Os 64 casos são os 48 candidatos do gate `forward_single_arm_v1` mais 16
mismatches preexistentes, predominantemente `Return(expr)` versus
`return expr`.

## Regras admitidas pelo oracle

As regras são aplicadas somente depois de a igualdade normalizada falhar:

1. `if condição then statement` e o bloco equivalente
   `if`/`statement`/`end if`, somente quando há um único token `then` não
   ambíguo;
2. parênteses em operandos booleanos completos, sem remover agrupamentos que
   alterem precedência entre `and` e `or`;
3. `return(expr)`/`return expr` e `destroy(expr)`/`destroy expr`, exigindo que os
   parênteses envolvam a expressão inteira;
4. declaração de nomes simples agrupada ou separada, sem inicializadores;
5. literais PowerScript equivalentes delimitados por aspas simples ou duplas.

Testes negativos mantêm diferentes guards, braços, literais, inicializadores e
precedências booleanas como mismatch. O conjunto completo passou com 168
testes.

Cada `function_comparison` v8 conserva `result = verified`, mas acrescenta
`verification_basis`. Os resumos do relatório também expõem contadores
separados. Isso preserva `function_reconstruction` como métrica principal sem
misturar as duas formas de evidência.

Relatórios reproduzidos:

- `pb2022-analysis/whole-function-v8-exmmain/decode-report.json`;
- `pb2022-analysis/whole-function-v8-appexmfe/decode-report.json`;
- `pb2022-analysis/whole-function-v8-pfcapsrv/decode-report.json`;
- `pb2022-analysis/whole-function-v8-transitions.json`.

## Investigação independente das constantes

A investigação usou o PBL compilado, os objetos `.udo` extraídos, os registros
de propriedades compiladas e a biblioteca de runtime em `pbvm.dll`. O fonte
conhecido foi usado somente no fim para conferir qual alias o autor havia
escrito; não alimentou o decompilador nem os catálogos binários.

O P-code dos 42 casos empilha o literal (`PUSH_CONST_INT`,
`PUSH_CONST_LONG` ou literal string). Portanto o ponto de uso não contém uma
referência ao nome. Porém, os objetos compilados preservam propriedades
constantes com:

- nome;
- tipo;
- flag `is_constant`;
- valor numérico ou offset para o buffer de valores string.

Isso produz três estados distintos:

| Recuperabilidade do nome original | Casos | Evidência |
|---|---:|---|
| Candidato único nos metadados compilados | 33 | 25 cores, 6 filetypes, `CACHE_ID` e `IS_PFCKEY`. |
| Valor recuperável, mas aliases indistinguíveis | 8 | 6 cores e as strings `DATABASE`/`FILE`. |
| Nome não demonstrado nos artefatos disponíveis | 1 | `FAILURE` compilado como `-1`. |
| **Total** | **42** | |

### Catálogos preservados

- `pfc_n_cst_apppreference.udo` contém
  `CST_FILETYPE_REG = 1`, `CST_FILETYPE_INI = 2` e
  `CST_FILETYPE_XML = 3`. Os seis usos têm mapeamento único.
- `pfc_n_cst_platformattrib.udo` contém o catálogo `COLOR_*`; o tipo compilado
  de `invo_constants` é `n_cst_platformattrib`, permitindo localizar esse
  catálogo sem consultar o fonte.
- `pfc_n_cst_lvsrv_datasource.udo` contém `CACHE_ID` e `IS_PFCKEY`, com offsets
  distintos para seus valores string.
- `pfc_n_cst_error.udo` contém `DATABASE` e `ICS_DATABASE` apontando para o
  mesmo valor, e `FILE` e `ICS_FILE` apontando para o mesmo valor.

As seis ambiguidades de cor são:

| Literal | Candidatos compilados |
|---:|---|
| 0 | `COLOR_SCROLLBAR`, `COLOR_MIN` |
| 1 | `COLOR_BACKGROUND`, `COLOR_DESKTOP` |
| 15 | `COLOR_BTNFACE`, `COLOR_3DFACE` |
| 16 | `COLOR_BTNSHADOW`, `COLOR_3DSHADOW` |
| 20 | `COLOR_BTNHIGHLIGHT`, `COLOR_3DHIGHLIGHT`, `COLOR_3DHILIGHT`, `COLOR_BTNHILIGHT` |
| 28 | `COLOR_GRADIENTINACTIVECAPTION`, `COLOR_MAX` |

Nesses oito casos ambíguos, o nome exato escrito originalmente não pode ser
deduzido do ponto de uso. Qualquer alias do mesmo catálogo e valor seria
semanticamente equivalente, mas não seria evidência de identidade com o fonte.

Para `FAILURE`, a busca exata não encontrou uma propriedade constante
correspondente no objeto, no `pfcapsrv.pbl` compilado ou na biblioteca de
runtime disponível. A ocorrência textual `failure` em `_typedef.grp` faz parte
de `corbacommfailure` e não comprova o símbolo global. Sem uma fonte normativa
independente da linguagem, `-1` deve permanecer literal e a perda do nome deve
ser classificada como informação de fonte eliminada, não erro semântico.

## Limite atual e próximo gate

O parser já lê o buffer global de valores durante a análise estrutural, mas o
descarta; propriedades string guardam hoje apenas o offset com high bit. Antes
de qualquer substituição simbólica, seria necessário:

1. reter e decodificar esse buffer no modelo compilado;
2. carregar constantes, owner types e herança no catálogo de membros;
3. resolver somente candidatos únicos no contexto tipado;
4. manter literals quando houver aliases ou contexto insuficiente;
5. permitir que o oracle compare símbolo e literal pelo valor obtido do
   binário, sem exigir que a saída use o símbolo.

Nenhuma substituição simbólica foi implementada neste gate.

O gate subsequente de buffer global e catálogo tipado foi concluído em
[`PB2022_COMPILED_CONSTANT_CATALOG_GATE.md`](PB2022_COMPILED_CONSTANT_CATALOG_GATE.md).
Ele preserva a proibição de substituição simbólica enquanto prova a
decodificação das strings e os resultados `zero`/`unique`/`ambiguous` usando
somente artefatos compilados.
