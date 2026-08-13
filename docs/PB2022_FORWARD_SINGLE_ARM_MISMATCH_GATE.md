# PB2022 `forward_single_arm_v1` mismatch gate

## Objetivo e escopo

Este gate classifica as 96 funções de fonte conhecida nas quais
`forward_single_arm_v1` foi aplicado, mas `function_reconstruction` ainda
terminou como `normalized_body_mismatch`.

O caso adjacente `pfc_n_cst_error.of_setlogfilestyle`, cujo `if` está dentro de
um `choose case`, foi mantido fora do conjunto. Assim, a população analisada é
exatamente a família de 96 funções pedida, e não o total bruto de 97 mismatches
estruturados do relatório.

Nenhuma regra de CFG, expressão ou statement foi promovida ao decompilador
neste gate. Em particular, o padrão de dois guards não foi implementado.

## Métrica de controle

Os relatórios de produção continuam em:

| Estado | `function_reconstruction = verified` | Total | Taxa |
|---|---:|---:|---:|
| Antes de `forward_single_arm_v1` (v3) | 380 | 1.873 | 20,29% |
| Estado atual (v6) | 431 | 1.873 | 23,01% |

A comparação nominal dos conjuntos v3 e v6 encontrou 51 funções promovidas e
zero funções anteriormente verificadas que tenham regredido. Como este gate é
somente analítico, o número oficial permanece 431; equivalências encontradas
abaixo são oportunidades, não novas verificações de produção.

## Método reproduzível

O script
[`scripts/analyze_forward_single_arm_mismatches.ps1`](../scripts/analyze_forward_single_arm_mismatches.ps1)
carrega os três relatórios v6, seleciona as funções estruturadas com
`forward_single_arm_v1`, exclui o `choose` adjacente e alinha os statements da
prévia com o fonte PB2022 conhecido por LCS.

Ele produz
`pb2022-analysis/forward-single-arm-v1-mismatch-analysis.json`, contendo a
classificação por função, os primeiros pontos de divergência e duas visões:

1. a primeira causa-raiz visível no corpo normalizado atual;
2. o que ainda sobra depois de uma canonicalização conservadora executada
   apenas pela análise.

A canonicalização experimental aceita `if` inline ou em bloco, parênteses
redundantes em condições, `return(expr)`/`return expr`,
`destroy(expr)`/`destroy expr`, declarações agrupadas/separadas e strings PB
com aspas simples ou duplas. Ela não altera o oracle de produção.

## Famílias de causa-raiz

Classificação mutuamente exclusiva pela primeira causa demonstrável:

| Família | Casos | Evidência principal |
|---|---:|---|
| Constante simbólica eliminada | 39 | O fonte usa constantes nomeadas; o P-code conserva somente o valor literal. |
| `if` inline versus forma em bloco | 37 | Mesmo guard e mesmo statement; difere apenas a forma textual da construção. |
| Grafia equivalente de expressão | 10 | Parênteses redundantes, sobretudo em predicados como `x = ""`. |
| Construção do fonte otimizada/omitida | 3 | Inicialização default, `destroy` ou `call super` não aparecem integralmente no P-code observado. |
| Normalização de literal com aspas simples | 3 | O normalizador atual protege apenas strings com aspas duplas. |
| Acesso de atributo DataWindow rebaixado | 1 | `dw.object.col[row]` reaparece como helper interno `__get_attribute_item(...)`. |
| Mapeamento de `ClassDefinition` | 1 | `.classdefinition` reaparece como `.getclassdefinition()`. |
| Scaffolding do compilador não colapsado | 1 | Temporários/declarações gerados em torno de `call super` permanecem na saída. |
| Declaração agrupada versus separada | 1 | Uma declaração PB com dois nomes reaparece como duas declarações. |
| **Total** | **96** | |

Essa visão atribui apenas uma causa por função. Três dos 37 casos de `if`
inline também contêm constantes simbólicas. Por isso, a distribuição mais útil
para decidir o próximo trabalho é a distribuição residual abaixo.

## Distribuição depois de canonicalização segura de forma

| Resultado analítico | Casos | Interpretação |
|---|---:|---|
| Resolvido somente por canonicalização de forma | 48 | 34 `if` inline, 10 grafias equivalentes, 3 strings com aspas simples e 1 declaração agrupada. |
| Constante simbólica eliminada | 42 | 39 casos primários mais 3 que também tinham `if` inline. |
| Construção do fonte otimizada/omitida | 3 | Não é recuperável genericamente apenas ampliando o CFG. |
| Scaffolding do compilador não colapsado | 1 | Regra de statement/call-super. |
| Mapeamento de `ClassDefinition` | 1 | Regra de expressão/acessor. |
| Acesso de atributo DataWindow rebaixado | 1 | Regra de expressão DataWindow. |
| **Total** | **96** | |

Os 48 casos da primeira linha tornam-se iguais ao fonte conhecido sob a
canonicalização analítica, mas **não** foram promovidos a
`function_reconstruction = verified`. Para isso, cada transformação ainda deve
ser incorporada ao oracle de forma explícita, coberta por testes positivos e
negativos e reexecutada nos três corpora.

Se esses 48 casos forem posteriormente admitidos e confirmados pelo oracle, o
máximo imediato seria 479/1.873 (25,57%), ganho de 48 funções ou 2,56 pontos
percentuais. Esse número é projeção, não resultado atual.

## Evidências representativas

- Em 34 funções, `if condição then return ...` no fonte e a forma
  `if ... then` / `return ...` / `end if` reconstruída têm o mesmo guard e o
  mesmo braço. Isso é diferença de forma do fonte, não falta de aresta no CFG.
- Em dez funções, o primeiro mismatch é uma diferença como
  `if IsNull(x) or x = "" then` versus
  `if isnull(x) or (x = "") then`.
- As 42 perdas de símbolo concentram-se em 31 funções de cores
  (`invo_constants.COLOR_*` versus números), seis usos de
  `CST_FILETYPE_REG/INI/XML`, dois usos de constantes string
  (`DATABASE`/`FILE`) e três constantes que coexistem com `if` inline
  (`CACHE_ID`, `IS_PFCKEY` e `FAILURE`).
- `pfc_n_cst_mru.of_getitem` contém a lacuna DataWindow;
  `pfc_n_cst_luw.of_isselfupdatingobject`, a lacuna `ClassDefinition`; e
  `w_examplemain.pfc_mrurestore`, scaffolding em torno de `call super`.
- `pfc_n_cst_tree.of_get`, `pfc_n_cst_tree.of_remove` e
  `w_examplemain.ue_printtree` são os três casos em que parte do fonte foi
  otimizada ou omitida. Em `ue_printtree`, por exemplo, o `call super` do fonte
  conhecido não possui instrução `CALL_SUPER` correspondente no P-code
  observado, portanto não pode ser inferido com segurança por uma regra geral.

## Decisão do gate

O próximo ganho comprovável **não está em ampliar o CFG**. Os 96 casos são
dominados por expressões, statements e critérios de equivalência do oracle:

1. primeiro, promover incrementalmente a canonicalização segura de forma,
   medindo quantos dos 48 candidatos passam a `verified` sem perda no conjunto
   atual de 431;
2. depois, tratar recuperação/apresentação de constantes simbólicas com tabelas
   ancoradas nos fontes PB2022 conhecidos, começando pelos grupos de alta
   repetição;
3. então, abordar separadamente DataWindow, `ClassDefinition`, scaffolding de
   `call super` e construções ausentes do P-code;
4. somente reavaliar novos padrões de control flow a partir da distribuição de
   mismatches restante.

O padrão de dois guards permanece deliberadamente fora deste gate.
