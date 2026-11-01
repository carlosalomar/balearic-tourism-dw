-- Spain / abroad, the residence split shared by hotel demand and the market dimensions.
select residence_key, residence_code, residence_name
from {{ ref('residence') }}
