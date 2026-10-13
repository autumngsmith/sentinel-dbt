{% docs __overview__ %}

#  Sentinel-2 Monster Model      
#### _One config-driven union model over 12 location sources._

## Contents:
1. Data Solution Pipeline
1. Modeling layers
1. Style Guide         

---------------------

## Pipeline

```
CDSE STAC API          Sentinel-2 L2A scene metadata, official ESA catalog
      ↓
fetch_scenes.py        one CSV per location in `data/raw/`, never edited
      ↓
load_raw.py            one DuckDB table per location: `locations.<location>`
      ↓
stg__<location>        unpacks the statistics JSON, dedupes to one row per capture
      ↓
fct_location_daily_metrics   unions every location; driven by the `locations` seed
```

### Notes     

* **`regions` seed**: the location and tile list for the fetch and load scripts. Not used by any model.
* **`locations` seed**: one row per location. Adding a location is a seed row, a source table, and a staging model.

----------------

## Modeling Layers

#### Mart Layer
Business-facing entities and facts ready for analysis.    

- Naming convention: `fct_{description}` (facts) or `dim_{description}` (dimensions).
- Materialized as table.


#### Intermediate Layer

Transformations that span multiple source tables but are not yet business-facing entities.    

Naming convention: `int_{description}`.


#### Staging Layer

Raw data is cleaned and standardized here. 
* Subdirectories are organized by source.
* Naming convention: `stg__{location}`.

The staging layer is divided by source. 

#### Other directories

- **analyses**: Ad-hoc SQL queries for analysis, not materialized in the database.
- **macros**: Custom Jinja macros to extend dbt functionality.
- **seeds**: CSV files used to load static data.
- **snapshots**: Type 2 Slowly Changing Dimensions (SCD) for tracking data changes over time.
- **tests**: Custom data integrity tests.
- **notebooks**: Jupyter notebooks used for more detailed documentation.    

-----------

## Style Guide

#### Model Naming
* Naming of all models should be in snake_case (where there is an underscore between each word).
    * `this_line_is_in_snake_case`
    * `thislineisnotinsnakecase`
* **For this project, the source is omitted from the naming convention.** Everything else stays the same. Models should be named with the modeling layer, source, and context. The layer and source should be prefixed by two underscores.
    * `<modeling layer>_<source>__<context>` -- there are TWO underscores between 'source' and 'context'
    * `int_stripe__charges.sql`
    * `fct_stripe__statement_summary.sql`
* Yaml files in a subfolder should be named as follows:. 
    * `__models.yml`
* All objects should be plural, such as: `stg_stripe__invoices`; realistically, you would never have a single 'order' in an orders table. 
* Marts are categorized between fact and dimensions with a prefix that indicates either, such as: fct_orders or dim_customers

#### Model Configuration
* For this project, staging and intermediate models are views; marts are tables. 
* In-model configurations should be specified like this: 
{% raw %}
```
{{ config(
    materialized = 'view'
) }}
```
{% endraw %}
* If a particular configuration applies to all models in a directory, it should be specified within the dbt_project.yml file.

#### Column Naming
* Naming of all columns should be in snake_case (where there is an underscore between each word).
    * `snake_case_id`
    * `notsnakecaseid`
* Names should be based off of business terminology, not source terminology. 
    * avoid naming a field `typecode` and instead name it `job_type`
    * avoid leaving columns with the name name, give those columns a more meaningful title such as `market_segment_name`
* Booleans should be prefixed with `is_` or `has_` 
* Consistency is key! Especially at the mart layer, use the same field names across models where possible. 

#### CTE's
* All {% raw %}`{{ ref('...') }}`{% endraw %} statements should be placed in CTEs at the top of the file
* Where performance permits, CTEs should perform a single, logical unit of work.
* CTEs with confusing or noteable logic should be commented
* CTEs that are duplicated across models should be pulled out into their own models
* Create a final or main CTE that you select from as your last line of code. This makes it easier to debug code within a model (without having to comment out code!)

``` md
{% raw %}

with first_ref_model as (
    select * from {{ ref('first_model') }}
), 
second_ref_model as (
    select * from {{ ref('second_model') }}
), 
-- comments about the join_two_,models CTE go here
pivot_first_model as (
    select * 
    ... pivot the model
    from first_ref_model
), 
-- this should be the last cte
final as (
    select * 
    from pivot_first_model
    left join second_ref_model on 
        second_ref_model.pk = pivot_first_model.fk
)
select * from final
{% endraw %}
```

#### SQL Writing Guide
* Do not optimize to decrease the number of lines of code. Newlines are cheap, but brain time is expensive! _(Please make your sql easier for yourself and others to read.)_

#### YAML Writing Guide
* Indents should be two spaces
* List items should be indented
* Use a new line to separate list items that are dictionaries where appropriate
* Lines of YAML should be no longer than 80 characters.
    * Use the > notation to add longform descriptions
* Example YAML:

``` yml
version: 2
models:
  - name: events
    description: This is a model about events
    columns:
      - name: event_id
        description: > 
            This is a unique identifier for the event
            
            This is a new line in a long form description; two new lines are needed for the new line to render in documentation
          tests:
          - unique
```

#### Jinja Writing Guide
* When using Jinja delimiters, use spaces on the inside of your delimiter, like {% raw %} {{ this }} instead of {{this}} {% endraw %}
* Use newlines to visually indicate logical blocks of Jinja



{% enddocs %}