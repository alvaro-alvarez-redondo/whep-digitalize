"""Postpro / rule_engine — ports ``r/2-postpro_pipeline/23-postpro_rule_engine/``.

The algorithmic heart: match dataset rows on ``column_source``/``value_source_raw`` (and
an optional ``column_target``/``value_target_raw`` guard), then rewrite source and update
target via a strategy. Every by-reference ``data.table::set`` becomes a functional polars
scatter (join-back + ``when/then``).

Status (risk):

* ``matching_strategy.py`` <- ``23-matching-strategy.R`` — **[done]** key encoding
  (NA -> ``na_match_key``), strategy config, tokenized target columns (``footnotes``,
  ``notes``). (MEDIUM)
* ``matching_values.py`` <- ``23-matching-values.R`` — **[done]** tokenized ``;``-membership
  match, order-preserving concat merge, elementwise change count (drives convergence). (HIGH)
* ``target_apply.py`` <- ``23-target-apply.R`` — ``last_rule_wins`` (stable-sort + group-last)
  with overwrite-event emission, and ``concatenate``. (HIGH)
* ``conditional_group.py`` <- ``23-conditional-group.R`` — cartesian keyed join on
  ``source_key``, subset target-condition match, source+target scatter, audit. (HIGH)
* ``footnote_rules.py`` <- ``23-footnote-rules.R`` — explode ``;`` tokens -> match ->
  resolve (remove > replace > original) -> reconstruct. The hardest single port. (HIGH)
* ``schema_validation.py`` <- ``23-schema-validation.R`` — coerce/validate rules,
  duplicate/conflict checks, radix-ordered conditional dictionary. (MEDIUM-HIGH)
* ``payload_application.py`` <- ``23-payload-application.R`` — per-file orchestration:
  footnote rules first, then each conditional group. (LOW-MEDIUM)
"""

from __future__ import annotations
