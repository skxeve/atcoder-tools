#!/usr/bin/env php
<?
// Generated by {{ atcodertools.version }} {{ atcodertools.url }}  (tips: You use the default template now. You can remove this line by using your custom template)
{% if mod %}
const MOD = {{ mod }}  # type: int
{% endif %}
{% if yes_str %}
const YES = "{{ yes_str }}"  # type: str
{% endif %}
{% if no_str %}
const NO = "{{ no_str }}"  # type: str
{% endif %}
{% if prediction_success %}
function solve({{ formal_arguments }})
{
}

{{ input_part }}
solve({{ actual_arguments }});
{% else %}
// Failed to predict input format
$inputs = [];
while (($item = fgets(STDIN)) !== false) {
    $inputs[] = $item;
}
{% endif %}
