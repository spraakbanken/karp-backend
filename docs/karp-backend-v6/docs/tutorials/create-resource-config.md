# Create a Resource Config

In this tutorial we are going to create a resource config for the resource `Lex Lex`.

## `resource_id` [required]

We need to define the `resource_id` for our resource, this will be used when we call the api.
The `resource_id` can't contain whitespace and should preferrable only contain lowercase letters.

```
lex_lex_config = {
    "resource_id": "lexlex"
}
```

## `resource_name` [optional]

We could also define the `resource_name` for our resource, if not the `resource_id` will be used.

```
lex_lex_config = {
    "resource_id": "lexlex"
    "resource_name": "Lex Lex"
}
```

## `fields` [required]

Here we define the fields that the entries in the resource will have.
The fields are defined by `"<field_name>": {"type": "<field_type>"}` where field_type can be any of:

| field_type | python_type | comment |
| ---------- | ----------- | ------- |
| `string`   | `str`       | smaller kind of string
| `long_string` | `str` | larger kind of string, exact limit?
| `boolean` | `bool` |
| `integer` | `int` |
| `number` | `float` |
| `object` | `dict` | requires the field `fields` that define fields

So we can a field `baseform` of type `string`:

```
lex_lex_config = {
    "resource_id": "lexlex",
    "resource_name": "Lex Lex",
    "fields": {
        "baseform": {"type": "string", "required": true}
    }
}
```

As we can see, we also said that this field is required, by adding the field in the `required` with value `true`.

Currently `array`:s are specified by defining the type and and then adding the field `collection` as in:

```
lex_lex_config = {
    "resource_id": "lexlex",
    "resource_name": "Lex Lex",
    "fields": {
        "baseform": {"type": "string", "required": true},
        "tags": {"type": "string", "collection": true}
    }
}
```

