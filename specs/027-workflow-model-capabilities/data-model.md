# Data model: F27

## CapabilityEntry
profile (str), path (str), capability (text_to_image | reference_edit | wan_flf2v | upscale | null), workflow (str), workflow_sha256 (recorded), actual_sha256 (str | null), roles {role: {node_id, input, class_type}}, outputs [kind], node_classes [str], models [ModelRef], constraints {role: {min, max, step}}, length_rule ("4n+1" for wan_flf2v), problems [{status, message}], status (one of 7), approval_needed [str].

## ModelRef
folder, file, role (diffusion | text_encoder | vae | checkpoint | lora | upscaler | clip_vision), licence, source, sha256 (catalogue value or "NOT RECORDED"), present (true | false | null).

## Preview
current {profile, capability, workflow_sha256}, candidate {...}, changes [{type: role_added | role_removed | role_moved | constraint_changed | output_changed | capability_changed | required_role_missing | model_added | model_removed | hash_changed, role?, before?, after?}], verdict (compatible | needs-rebinding | incompatible).

## SelectionRecord (`configs/registry/selection.json`)
schema 1; active {capability: {profile, workflow_sha256}}; history [{utc, action: select | rollback, capability, previous {profile, workflow_sha256} | null, new {...} | null, note}]. History is append-only. Rollback sets active to the `previous` of the most recent selection still in effect (null → production default) and appends a rollback entry.
