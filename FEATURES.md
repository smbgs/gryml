
# Gryml Features

### Com-tags

**Status:** alpha

**Details:** 
Core functionality of Gryml. Ability to save the original syntax and structure of the yaml file by using native yaml
comments ("com-tags") for templating. Com-tags are defined as `#[value-strategy argument]{expression}`, where all
parts are optional.

Com-tags can be used at the end of the line:

```yaml
key: default_value #{new_value}
```

Com-tags can also be used above the line:

```yaml
#[if value]
key: value
```

Multiple com-tags can be applied (without empty lines): 

```yaml
#[if value]
#[map value]
key: value
```

### Expressions

**Status:** alpha

**Details:**
Com-tags may use expressions based on the Jinja 2 expression engine. Values tree can be used
in the expressions. 

Example:

- `{some.value == other.value and (third.value <= 10)}`

### CLI Values

**Status:** beta

**Details:** 
Ability to set multiple values with the following arguments: `--set a.b.c=value`, where "a.b.c" is the path to the value
in the value tree. 

### Values files 

**Status:** beta

**Details:** 
Ability to define the value tree in the additional yaml file.  
Com-tags are also immediately evaluated upon declaration in the values files allowing for complex
implementation scenarios.

### Values file "gryml" object

**Status:** beta

**Details:** 
Additional meta-data may be defined in the values file with the key: `gryml`. 
More features define their own keys in the `gryml` object.

### Nested values files including
 
**Status:** beta

**Details:** Ability to import additional value files before importing values file. Uses the current
values tree and supports com-tags in values files. 

Gryml object field `"include"`:
 
- `gryml.include: [<yaml-file-path>]`

### Nested values files overrides
 
**Status:** beta

**Details:** 
Similar to the "Nested values files including" but applies after the all com-tags in the values
file were calculated.

Gryml object field `"override"`:

- `gryml.override: [<value-file-path>, ...]`

  
### Output files  
 
**Status:** beta

**Details:** 
This feature helps to implement complex dependency graphs. Single values file may be used to
"output" multiple files using the same values tree in the com-tags for all of them.

Depending on dynamic conditions, additional yaml files can be either included or excluded from
the output.

In combination with the *"Nested values files including"* feature it's possible to implement
robust dynamic "chart"-like configurations.

Gryml object field `"output"`:

- `gryml.outut: [<yaml-file-path>, ...]`

### File path prefixes

**Status:** draft

**Details:** 
Ability to define and use `@<prefix>/path/to/file.yaml` in addition to relative and absolute
paths for value files including, overrides and output files.  

### Conditional strategies 

**Status:** beta

**Details:** Ability to use if/else conditions to remove parts of the YAML file.  

- `#[if condition]{value}[else]{another.value}` - full syntax
- `#[if]{value}[else]{another.value}` - shorter syntax
- `#[if]{value}` - shortest

### Repeat strategies & list-item com-tags

**Status:** alpha

**Details:** Ability to repeat the list item with additional dynamic values from lists or objects.
Generates 2 arguments with the provided index and value (if the value is object - index is the key)

```yaml
#[repeat key:value]{value}
- name: default-value #{$key}
  data: some-data #{$value}
```  

### Inline templating

**Status:** draft

**Details:** Ability to use Jinja (or some other) templating language in text blobs with 
the current values tree.

```yaml
#[template]
data: |
 #!/bin/env bash 
    
 {if values}
    echo ${some-value}   
 {else}
    echo ${other-value}
 {fi}
```

### Value pipes

**Status:** alpha

**Details:**
 Ability to use named functions with parameters to transform values

`{value|base64e}` - encodes the value as base64 string  

### Common value pipes

**Status:** draft
**Details:**
 Ability to define dynamic value pipes as expressions in values files.

### Template value pipes

**Status:** draft

**Details:** Ability to use pipes for well-known file types instead of templates for
target generation. 

Pipes can use pre-defined or user-defined templates to generate text instead of inline
templates. 

For example it's possible to generate simple .ini files from a simple part of the value-tree.
It's also possible to generate derived yaml but store it as a string.

 


