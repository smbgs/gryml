
# Gryml

## WARNING: this is the early development version not suitable for use by anyone!

Sometimes you just need to substitute a couple of variables in the K8S resource definition.  

This tool was born as an attempt to bridge the gap between HELM and Kustomize as they both
are lacking simplicity for trivial but common cases. 

While Gryml was designed with k8s in mind it is essentially a general purpose YAML processor, and can be used to
automate the generation of any yaml files when value substitution is needed.


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
  name: "application" #{app-{common.name}-suffix}
``` 

The `name` field with the default value `"application"` has the `#{app-{common.name}-suffix}` Gryml tag. 

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

 `#[strategy]{value.path}`
 
 where supported `strategy` is one of the following:
 
 - `set` - (default) - replaces the whole value 
 - `append` - adds new array items to the existing array value
 - `merge-using <key>` - merges two array values containing objects using the values of the fields `<key>` in both 
    collections to find and replace existing items 
    
 - **More strategies are TBD**     

   
## Value files

If the configuration is complex in addition to `--set` flags Gryml supports `values file`. You can use the 
`-f <path_to_values_file>` argument to use the YAML value file in combination with the `--set` arguments. Note that
`--set` arguments will override values file.

Additionally, values file provide two important features, making Gryml capable of producing quite complex
configurations similar to HELM charts via `Gryml directives`.

Gryml directives can be defined in the list with the key `"gryml"` in a values file.

### Import directive

Import directive is defined as an object with the `"import"` key and a string value - a path to the additional 
values file that will be also included (path can be relative to the values file or absolute). 

Note that multiple `"import"` directives are supported.

For example:

```yaml
gryml:
 - import: "another.values.yml"
 - import: "/workspace/root.values.yml"
```

Note: Additional values files are imported **before** the current file and values are merged.   

Note: Gryml tags can also be used in the imported files (initial value tree can be setup using `--with` arguments that 
are very similar to the `--set` arguments, but will be overwrote by the values files.). 

### Source directive

Source directive is defined as an object with the `"source"` key and a string value - a path to the additional 
yaml file that will be also processed and included in the output **after** all values files and `--set` arguments are 
processed and a final value tree has been built. 

Note that multiple `"source"` directives are supported.

In combination with the `import` directives this allows different outputs to be generated from a single codebase 
based on the different initial values files. Moreover, resource definitions can be logically organized into libraries
and artifacts in a single or even multiple repositories and then combined together explicitly in a values file. 

This basically provides a way to generate "charts" dynamically, both significantly reducing the amount of duplicated
code between different resource definitions, while deriving the related parts from same values. 

### Value transformation pipes 

TODO: describe value transformation pipes

## Conditional values

Are not supported yet and might not be supported. We'd like to avoid conditional configuration as much as possible.
   

## Chart management and migrating from HELM

Unlike HELM, Gryml currently does not add any labels into generated resource definitions and is not capable of managing
the release versions. It's unclear if we  will support this approach in future, but we want to introduce some
quality of life improvements for `kubectl` users.



## Advanced examples

### Value Strategies 

Lets look at this `Deployment` definition with already added Gryml tags.

`deployment.gryml.yml`
 
```yaml
apiVersion: apps/v1 #{api-version.deployment}
kind: Deployment
metadata:
  name: "application" #{prefix-{name}-suffix}
spec:
  replicas: 1 #{requests-replicas}
  strategy:
    type: Recreate
  selector:
    matchLabels:
      application: "application" #{name}
  template:
    metadata:
      labels:
        application: "application" #{name}

    spec:
      serviceAccountName: serviceAccount #{service-account-name}
      containers:
        - name: application-main #{main-{name}-{role}-container}
          image: image #{{image}:{tag}}

          env: #[merge-using name]{env.common}
            - name: DEMO_GREETING
              value: "Hello from the environment"
            - name: DEMO_FAREWELL
              value: "Such a sweet sorrow"
        - name: application-secondary #{secondary-{name}-{role}-container}
          image: image #{{image2}:{tag}}

          env: #[append]{env.common}
            - name: DEMO_FAREWELL
              value: "Such a sweet sorrow"

        - name: application-third #{secondary-{name}-{role}-container}
          image: image #{{image3}:{tag}}
```  
 
 Now lets create the values file (this part is very similar to HELM):
 
 `values.gryml.yml`
 
 ```yaml
api-version:
  deployment: 'apps/v1'

name: 'custom-name',
image: 'custom-image'
tag: 'latest'

replicas: 2
service-account-name: 'custom-service-account'

env:
  common:
    - name: "COMMON_GREETING"
      value: "Common hello"
    - name: "DEMO_GREETING"
      value: "Hello from the custom environment"
```


### Context variables

TODO: implement and describe derived context variables

### Local variables

TODO: implement and describe local variables  

## Library

TBD: Gryml will be packaged and available via pypi.
