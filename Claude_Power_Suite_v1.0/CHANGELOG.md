# Changelog

Formato baseado em Keep a Changelog; versionamento semântico.

## [1.0.0] - 2026-11-01

### Adicionado
- Skill `orchestrating-power-suite`: roteamento, pacote de contexto entre
  etapas e pipelines padrão.
- Skill `engineering-prompts` com `scripts/lint_prompt.py` e catálogo de
  padrões por tipo de problema.
- Skill `authoring-agent-skills` com `scripts/scaffold_skill.py`,
  `scripts/validate_skill.py` e referência de especificação por superfície.
- Skill `architecting-software` com `scripts/new_adr.py` e catálogo de
  atributos de qualidade.
- Skill `reviewing-code` com `scripts/diff_hotspots.py` e checklist por
  categoria e linguagem.
- Skill `debugging-systematically` com `scripts/log_signatures.py` e catálogo
  de causas por sintoma.
- Skill `writing-technical-docs` com `scripts/check_markdown.py` e templates
  por tipo de documento.
- Skill `analyzing-tabular-data` com `scripts/profile_csv.py` e padrões de
  análise.
- Manifesto de plugin e marketplace do Claude Code.
- 24 cenários de avaliação (3 por skill) com arquivos de entrada.
- Ferramentas `tools/validate_suite.py`, `tools/package_skills.py`,
  `tools/install.sh` e `tools/run_trigger_evals.py` (mede acionamento real
  das skills via `claude -p`).
- Avaliação dos comportamentos esperados por LLM como juiz
  (`run_trigger_evals.py --judge`) e projeto de exemplo com defeitos
  plantados em `evals/files/projeto-exemplo/`.
- Ícone do plugin e licença MIT.
- Testes unitários em `tests/test_scripts.py`.
