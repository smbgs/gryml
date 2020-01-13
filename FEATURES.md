
# Gryml Features

### Com-tags

**Status:** alpha

**Details:** 
Core functionality of Gryml. Ability to save the original syntax and structure of the yaml file by using native yaml
comments ("com-tags") for templating. Com-tags are defined as `#[value-strategy argument]{expression}`, where all
parts are optional.



### CLI Values

**Status:** beta

**Details:** 
Ability to set multiple values with the following arguments: `--set a.b.c=value`, where "a.b.c" is the path to the value
in the value tree. 

### Values files 

**Status:** beta

**Details:** 
Ability to define the value tree in the additional yaml file.  
Com-tags are also immediately evaluated upon declaration.

### Values file "gryml" object

**Status:** beta



### Nested values files Including
 
**Status:** beta

**Details:** Ability to import additional value files before importing values file. Uses the current
values tree and supports com-tags in values files. 

Syntax applies to the values files, root level: 
 
- `gryml.include: [<yaml-file-path>]`

### Nested Values Files Overrides
 
**Status:** beta

- `gryml.override: [<value-file-path>, ...]`

  
### Nested YAML Files Importing 
 
**Status:** needs minor rework

**Details:** Ability to add more YAML files for processing and output from values files. 


### Nested Values Templating 
 
**Status:** needs rework

**Details:** Ability to dynamically apply values tree in com-tags during the processing of the values files.

### Value expressions in strategies and values

**Status:** draft
**Details:** Ability to safely evaluate simple logical expressions with values in places where values can be used 

- `{some.value == other.value and (third.value <= 10)}`

### Conditional strategies 

**Status:** draft

**Details:** Ability to use if/else conditions to remove parts of the YAML file.  

- `#[if condition]{value}[else]{another.value}` - full syntax
- `#[if]{value}[else]{another.value}` - shorter syntax
- `#[if]{value}` - shortest

### Repeat strategies & list-item com-tags

**Status:** draft

**Details:** Ability to repeat the list item with additional dynamic values from lists or objects.
Generates 2 arguments with the provided index and value (if the value is object - index is the key)

```yaml
#[repeat key:value]{value}
- name: default-value #{$key}
  data: some-data #{$value}
```  

### Multiline com-tags

**Status:** draft

**Details:** Ability to use multiple com-tags that will be sequentially applied to the target 

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

**Status:** needs improvements

**Details:** Ability to use named functions with parameters to transform values

`{value|base64e}` - encodes the value as base64 string  

### Template Value pipes

**Status:** draft

**Details:** Ability to use pipes for well-known file types instead of templates for
target generation. 

Pipes can use pre-defined or user-defined templates to generate text instead of inline
templates. 

For example it's possible to generate simple .ini files from a simple part of the value-tree.
It's also possible to generate derived yaml but store it as a string.

 


