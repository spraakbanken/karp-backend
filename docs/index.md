# Karp backend

Karp is a tool for editing structured data. It features:
- A frontend (not documented here)
- A CLI for batch updates of data and administrative tasks
- Version control
- A plugin system for adding new routes or automatic updates to data
- A web API for searching, editing, and fetching history

A data set in Karp is called a resource and a resource consists of a number of entries.
A resource is a collection of objects, which may be as simple as key-value pairs or
full trees, with support for sub-collections. Karp uses JSON to store and send the entries.

Karp is developed by [Språkbanken Text](https://spraakbanken.gu.se) at the University of Gothenburg. The code is open source and
available as a [Git repository](https://github.com/spraakbanken/karp-backend).

## OpenAPI / Redoc API specification

This documentation describes the Karp system. There is also a reference for the API:

- ReDoc interface: https://ws.spraakbanken.gu.se/docs/karp
- OpenAPI specification: https://spraakbanken4.it.gu.se/karp/v7/openapi.json

## Karp at Språkbanken

Språkbanken's Karp instance contains mostly lexical data, most freely available. It is possible
to use the web API, the frontend or our resource repository to use the data available.

- [API-reference](https://ws.spraakbanken.gu.se/docs/karp), API base URL https://ws.spraakbanken.gu.se/ws/karp/v7
- Frontend https://spraakbanken.gu.se/karp
- Data https://spraakbanken.gu.se/resurser/lexicon

## Table of contents

- [Installing the Karp backend](installation.md)
- [Karp's command line tool](cli_ref.md)
