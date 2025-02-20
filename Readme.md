# XML Request Parser

A Python-based XML request parser that processes hotel availability requests, validates the input data and returns JSON responses. 

## Features

- Parses XML requests for hotel availability
- Validates input data including dates, currency, nationality, and room occupancy
- Generates unique IDs for each request using timestamp and UUID
- Calculates selling prices with markup and currency exchange
- Handles multiple room configurations with adult/child validation
- Returns well-structured JSON responses

## Requirements

- Python 3.7+


## Installation




## Steps to run the code

1. Open the `xml_requests_parser.py` file in a text editor
2. Modify the `xml_request` variable with your XML string
3. Run the parser with: `python xml_requests_parser.py`
4. The JSON response will be printed to the console.



OR



1. Open any python terminal and run the following command:
2. from xml_requests_parser import XMLRequestParser
3. xml_request = """<your xml request here>"""
3. parser = XMLRequestParser()
4. print(parser.process_request(xml_request))

## Sample Request

xml

```
<AvailRQ xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<timeoutMilliseconds>25000</timeoutMilliseconds>
<source>
<languageCode>en</languageCode>
</source>
<optionsQuota>20</optionsQuota>
<Configuration>
<Parameters>
<Parameter password="XXXXXXXXXX" username="YYYYYYYYY" CompanyID="123456"/>
</Parameters>
</Configuration>
<SearchType>Multiple</SearchType>
<StartDate>23/02/2025</StartDate>
<EndDate>27/02/2025</EndDate>
<Currency>USD</Currency>
<Nationality>US</Nationality>
</AvailRQ>
```

## Sample Response

json

```
[
  {
    "id": "A#20250220153144-ebfaac82",
    "hotelCodeSupplier": "39971881",
    "market": "US",
    "price": {
      "minimumSellingPrice": null,
      "currency": "USD",
      "net": 132.42,
      "selling_price": 136.66,
      "selling_currency": "USD",
      "markup": 3.2,
      "exchange_rate": 1.0
    }
  }
]
```

## Test Cases

The `test_parser.py` file contains test cases for the parser. To run the tests, use:

```
python -m unittest
```


