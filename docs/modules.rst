Modules
========
The modules support the back-end interactions with an oTherm instance.   They are provided as examples only.

.. toctree::
   :maxdepth: 2


analysis
========
This set of analysis modules uses the oTherm APIs to access oTherm data. See the `API Documentation <https://otherm.org/api_documentation>
for more details. The more complex oTherm data is organized into dataclasses that use that are ready for analysis.  For example,

.. literalinclude:: ../db_tools/otherm_db_reader.py
   :start-after: sphinx-ThermalLoad-begin
   :end-before: sphinx-ThermalLoad-end



.. toctree::
   :maxdepth: 4

   analysis


db_tools
========
A collection of scripts that enable uploading and downloading of data from an oTherm instance

.. toctree::
   :maxdepth: 4

   db_tools
   
   
