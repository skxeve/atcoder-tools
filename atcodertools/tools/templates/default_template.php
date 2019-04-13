#!/usr/bin/env php
<?

$inputs = [];
while (($item = fgets(STDIN)) !== false) {
    $inputs[] = $item;
}

print_r($inputs);
