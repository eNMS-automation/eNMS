Service selection is a very important topic for use in understanding
how to design and build automation workflows.  Each of the service types
available to the system performs a specific action and has strengths and
weaknesses that should be known.

In network automation, often we are tasked with interacting with devices
or device components through interfaces that do not return structured
data.  Structured data refers to data obtained from the device that is
easily index-able to its individual elements. In other words, structured
data is data that does not need to be parsed, whereas unstructured data
must be parsed to isolate an individual data element. There also exists
semi-structured data which is structured but still needs some amount of
parsing to isolate data elements.

Note that eNMS uses structured data dictionaries internally to pass data
along the workflow from service to service. So, using eNMS, the user will
spend a lot of time considering how to either retrieve structured data
directly from the device or most-easily convert unstructured or semi-structured
data from the device to structured data.  This section will discuss and rate
the available built-in service types according to how work-intensive they are
for obtaining structured data. The user can refer to these rating when
considering which service to use for a particular action in the workflow.



Image: The Structured Data Pyramid

(Rated from Little-to-No Parsing Work needed to Most Parsing Work needed)


## Direct JSON or XML Command Output

In the case where the device is capable of giving a fully-structured data
response, there is no additional parsing needed. This is the best solution
possible.

