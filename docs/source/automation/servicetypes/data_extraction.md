Extract some data from the payload with a python query, and optionally
post-process the result with a regular expression or a TextFSM template.

![Data Extraction Service](../../_static/automation/builtin_service_types/data_extraction.png)

Configuration parameters for creating this service instance: 

- `Variable Name`: name to give the resulting variable in the results. 

- `Python Extraction Query`: a python query to retrieve data from the
   payload. 

- `Post Processing`: choose the type of post-processing: 

    - `Use Value as Extracted`
    - `Apply Regular Expression (findall)`
    - `Apply TextFSM Template`
    
- `Regular Expression/ TestFSM Template Text`: regular expression or
  TextFSM template, depending on the value of the \"Post Processing\". 

- `Operation` Choose the operation type: 

    - `Set/Replace`
    - `Append to a list`
    - `Extend List`
    - `Update dictionary`
    
!!! note
    The above list and dictionary operations allow for accumulated results
    through a workflow, such as each service adds something to the result
    variable that is then reported on at the end.

!!! note
    These same fields are replicated twice more, since the service can
    extract / post-process up to 3 variables

