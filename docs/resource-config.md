# The resource configuration file

The resource configruation file is the file that is given when creating a
new lexicon:

`resource create <path-to-config.json>`

It contains settings for the resource and descriptions of the fields used in
the resource's entries.

The following settings are available:

| key                                    | JSON type |
|----------------------------------------|-----------|
| [`resource_id`](#resource_id-required) | string    | 
| [`resource_name`](#resource_name-optional)| string    |
| [`fields`](#fields-required)| object    |
| [`id`](#id-required)| string    |
| [`sort`](#sort-required)| string    |
| `additionalProperties` | boolean   |


## `resource_id` [required]

We need to define the `resource_id` for our resource, this will be used when we call the api.
The `resource_id` can't contain whitespace and should preferrable only contain lowercase letters.

```json
{
  "resource_id": "parolelexplus"
}
```

## `resource_name` [optional]

We could also define the `resource_name` for our resource, if not the `resource_id` will be used.

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus"
}
```

## `fields` [required]

Here we define the fields that the entries in the resource will have.
The fields are defined by `"<field_name>": {"type": "<field_type>"}` where field_type can be any of:

| field_type    | python_type | comment                                        |
| ------------- | ----------- | ---------------------------------------------- |
| `string`      | `str`       |
| `boolean`     | `bool`      |
| `integer`     | `int`       |
| `number`      | `float`     |
| `object`      | `dict`      | requires the field `fields` that define fields |

### `required`

### Collections

If the field is a collection (i.e. array), add: `"collection": true` to the field
description.

### `fields` of `"type": "object"`

### Example

```json
{
  "resource_id": "parolelexplus",
  "fields": {
    "paroleID": { "type": "string", "required": true },
    "wordform": { "type": "string", "required": true },
    "partOfSpeech": { "type": "string" },
    "valency": { "type": "string" },
    "saldo": { "type": "string", "collection": true }
  }
}
```

## `id` [required]

Currently not used, but required to set.

## `sort` [optional]

Specifies the default field the results will be sorted by.

## `additionalProperties` [optional]

If `true`, only entries where all fields described in the configuration are accepted
when creating/modifying entries. Default: `false`
