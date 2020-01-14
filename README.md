
# Gryml

#### WARNING: Alpha version, might not be suitable for production 
#### WARNING: API is unstable and might change significantly

Sometimes you just need to substitute a couple of variables in the K8S resource definitions, often using the same
value in multiple files.   

This tool was born as an attempt to bridge the gap between HELM and Kustomize as they both
are lacking simplicity for trivial but common cases. But while Gryml was designed with k8s in mind it is essentially a general purpose YAML processor, and can be used to
automate the generation of any yaml files when value substitution is needed.

We provide [the full list of features](FEATURES.md) separately, but in this document we will cover the most important
ones.  

## Installation

Gryml is now available in the pypi (Python 3.7+ is required): 

- `pip install gryml`

And you should be able to use CLI version:
- `gryml --help`

Gryml supports UNIX pipes for both input and output so something like this is also possible:
 
```bash
$ echo "{say: something} #{world.greeting}" | gryml - --set world.greeting="hello world!"
---
say: hello world!
``` 

But generally you'll use Gryml to process existing template files as shown in the following section.

## Basics

Gryml can be used as Unix-style CLI to pipe the incoming file or directory combined with the values file or cmd args 
as a stream of K8S resource definitions to stdout.

This can be used to apply the modified definitions via kubectl: `gryml <file>|<dir> --set app.name=sample | kubectl apply -f -`

Gryml relies on YAML comments instead  of inline templates, which makes it compatible with the tools that can
only work with the native k8s resource definition files.

Lets look at the simple example:

`deployment.gryml.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "application" #{"app-" ~ common.name ~ "-suffix"}
``` 

The `name` field with the default value `"application"` has the `#{"app-" ~ common.name ~ "-suffix"}` Gryml tag. 

We can apply the value using the following command:

 `gryml deployment.gryml.yml --set common.name=simple`

This will result in the following output:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "app-simple-suffix" 
``` 

Note: if your value is simple and you just to use it as is - you can use the simplified tag version: `#{common.name}`.

Note: Multiple `--set` parameters can be used to set multiple values if necessary.

By default all values including objects and lists are replaced with the value of the simplified tag, but sometimes
it's necessary to combine static values from the resource definition file with some dynamic values. One of the most 
common use cases is the container environment variables.

To facilitate that, Gryml provides "value strategies" that can be applied using the following tag syntax:

 `#[strategy <argument?>]{expression}`
 
 where supported `strategy` is one of the following:
 
 - `set` - (default) - replaces the whole value 
 - `append` - adds new array items to the existing array value
 - `merge-using <key>` - merges two array values containing objects using the values of the fields `<key>` in both 
    collections to find and replace existing items
 - `if <expression>` - removes the value or item if expression evaluates as false      
 - `repeat <key:value?>` - iterates over values from the `expression` and repeats the array items     

   
### Value files

If the configuration is complex in addition to `--set` flags Gryml supports `values file`. You can use the 
`-f <path_to_values_file>` argument to use the YAML value file in combination with the `--set` arguments. Note that
`--set` arguments will override values file.

Additionally, values file provide two important features, making Gryml capable of producing quite complex
configurations similar to HELM charts via `Gryml directives`.

Gryml directives can be defined in the list with the key `"gryml"` in a values file.

### Importing other value files

It is possible to include additional values files using the `include` field of the `gryml` metadata object, 
for example:

```yaml
gryml:
 include: 
  - "another.values.yml"
  - "/workspace/root.values.yml"
```

Note: Additional values files are imported **before** the current file and values are merged, you can use
 `override` field of the `gryml` metadata object if you need to apply additional values **after** the current file was
 evaluated.      


### Output

It is possible to reference yaml 
yaml files that will be also processed and included in the output **after** all values files and `--set` arguments are 
processed and a final value tree has been built. 

In combination with the `include` and `override` directives this allows different outputs to be generated from a single 
codebase based on the different initial values files. Moreover, resource definitions can be logically organized into
libraries and artifacts in a single or even multiple repositories and then combined together explicitly in a values file.

This basically provides a way to generate "charts" dynamically, significantly reducing the amount of duplicated
code between different resource definitions, while deriving the related parts from same values. 

### Value transformation pipes 

Gryml value expressions support Jinja2 filters (we call them value transformation pipes though). Gryml also
defines a couple of additional pipes suitable for use with k8s.

TODO: describe value transformation pipes more.

### Conditional values

Are not supported yet and might not be supported. We'd like to avoid conditional configuration as much as possible.
   

## Chart management and migrating from HELM

Unlike HELM, Gryml currently does not add any labels into generated resource definitions and is not capable of managing
the release versions. It's unclear if we  will support this approach in future, but we want to introduce some
quality of life improvements for `kubectl` users.


## Advanced example

Lets look at this `Deployment` definition with already added Gryml com-tags.

`deployment.gryml.yml`
 
```yaml
apiVersion: apps/v1 #{apiVersion.deployment}
kind: Deployment
metadata:
  name: "application" #{"test-" ~ name ~ "-suffix"}
spec:
  replicas: 1 #{replicas}
  strategy:
    type: Recreate #{strategy}
  selector:
    matchLabels:
      application: "application" #{name}
  template:
    metadata:
      labels:
        application: "application" #{name}

    spec:
      serviceAccountName: serviceAccount #{serviceAccountName}
      containers:
        - name: main #{"main-" ~ roleContainerSuffix}
          image: image #{imageRef}

          env: #[merge-using name]{env.common}
            - name: DEMO_GREETING
              value: "Hello from the environment"
            - name: DEMO_FAREWELL
              value: "Such a sweet sorrow"
        
        #[if useSecondary]
        - name: secondary #{"secondary-" ~ roleContainerSuffix}
          image: image #{imageRef}

          env: #[append]{env.common}
            - name: DEMO_FAREWELL
              value: "Such a sweet sorrow"

```  
 
 Now lets create values files:

`base.gryml.yml`

```yaml
apiVersion:
  deployment: 'apps/v1'
```

`values.gryml.yml`
```yaml

gryml:
  include:
    - base.gryml.yml

  override:
    - context.gryml.yml
  
  output:
    - deployment.gryml.yml

name: 'custom-name'
role: 'test'
image: 'custom-image'
tag: 'latest'

useSecondary: false

replicas: 2
serviceAccountName: 'custom-serviceAccount'

env:
  common:
    - name: "COMMON_GREETING"
      value: "Common hello"
    - name: "DEMO_GREETING"
      value: "Hello from the custom environment"
```

`context.gryml.yml`
```yaml
# Note: dynamic derived values are supported using the com-tags
imageRef: = #{image ~ ":" ~ tag}
roleContainerSuffix: = #{name ~ "-" ~ role ~ "-container"}
```

Now you can just exec: `gryml -f values.gryml.yml`, as a result you should be able to see contents of the 
`deployment.gryml.yml` file with the substituted values.

## Best practices

- Avoid complex logic in the output yaml files and instead implement this logic in the values files
- Separate configuration between multiple values files instead of combining it into a single one


## Library

Gryml can easily be used as a python module without CLI:

```python
from gryml.core import Gryml
from pathlib import Path

gryml = Gryml()

values = gryml.load_values(
    Path("values-file.yaml"), 
    base_values=None, 
    process=True, 
    mutable=True,
    load_nested=True, 
    load_sources=True
)
```
