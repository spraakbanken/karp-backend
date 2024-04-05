# Create a Resource Config

In this tutorial we are going to create a resource config for the resource `parolelexplus`.

Some entries in this resource looks like this:

```json
{"wordform": "skyddsf\u00f6reskrift", "partOfSpeech": "nn", "valency": "(ATTR) [nn] (ATTR)", "paroleID": "US14440_15998"}
{"wordform": "arrangerar", "saldo": ["arrangera..1"], "partOfSpeech": "vb", "valency": "S_NP_A [vb] DO_NP_x (PO_PP_f\u00f6r_y)", "paroleID": "US675_727"}
{"wordform": "konstruktion", "saldo": ["konstruktion..1"], "partOfSpeech": "nn", "valency": "[nn] (PP_av_NP_x)", "paroleID": "US8133_8951"}
{"wordform": "kort", "saldo": ["kort..1"], "partOfSpeech": "av", "valency": "SUPR_[av]", "paroleID": "US8254_9087"}
{"wordform": "avmagrad", "saldo": ["avmagrad..1"], "partOfSpeech": "av", "valency": "[av] NP", "paroleID": "US909_978"}
{"wordform": "samlar", "saldo": ["samla..1", "samla..2"], "partOfSpeech": "vb", "valency": "S_NP_A [vb] DO_NP_x", "paroleID": "US13500_14968"}
{"wordform": "myser", "saldo": ["mysa..1"], "partOfSpeech": "vb", "valency": "S_NP_A [vb] (PO_PP_mot_B)", "paroleID": "US10239_11340"}
{"wordform": "s\u00e4krar", "saldo": ["s\u00e4kra..1"], "partOfSpeech": "vb", "valency": "S_NP_A/x [vb] DO_NP_y", "paroleID": "US16362_18148"}
{"wordform": "f\u00f6renlig", "saldo": ["f\u00f6renlig..1"], "partOfSpeech": "av", "valency": "[av] PP_med_NP_x", "paroleID": "US4828_5353"}
{"wordform": "hastighet", "saldo": ["hastighet..1"], "partOfSpeech": "nn", "valency": "(ATTR) [nn] (ATTR)", "paroleID": "US6093_6719"}
```

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
| `string`      | `str`       | smaller kind of string                         |
| `boolean`     | `bool`      |
| `integer`     | `int`       |
| `number`      | `float`     |
| `object`      | `dict`      | requires the field `fields` that define fields |

So we begin with adding config for the `paroleID` field of type `string`:

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus",
  "fields": {
    "paroleID": { "type": "string", "required": true }
  }
}
```

After we can handle all `string` fields:

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus",
  "fields": {
    "paroleID": { "type": "string", "required": true },
    "wordform": { "type": "string", "required": true },
    "partOfSpeech": { "type": "string" },
    "valency": { "type": "string" }
  }
}
```

`array`:s are specified by defining the type and then adding the field `collection` as in:

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus",
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

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus",
  "fields": {
    "paroleID": { "type": "string", "required": true },
    "wordform": { "type": "string", "required": true },
    "partOfSpeech": { "type": "string" },
    "valency": { "type": "string" },
    "saldo": { "type": "string", "collection": true }
  },
  "id": "paroleID"
}
```

## `sort` [required]

Specifies by which field the entry shall be sorted by.

```json
{
  "resource_id": "parolelexplus",
  "resource_name": "parolelexplus",
  "fields": {
    "paroleID": { "type": "string", "required": true },
    "wordform": { "type": "string", "required": true },
    "partOfSpeech": { "type": "string" },
    "valency": { "type": "string" },
    "saldo": { "type": "string", "collection": true }
  },
  "id": "paroleID",
  "sort": "wordform"
}
```
