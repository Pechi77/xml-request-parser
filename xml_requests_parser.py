import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

from constants import *

class XMLRequestParser:
    def __init__(self):
        # __define_ocg__ (Secret Handshake 😉)
        self.var_ocg = "OCG_SECRET"

    def parse_xml(self, xml_data: str) -> Dict[str, Any]:
        """Parses XML and extracts relevant fields with validation."""
        root = ET.fromstring(xml_data)
        
        # Extract values with defaults
        language = root.findtext(".//source/languageCode", DEFAULT_LANGUAGE)
        options_quota = int(root.findtext(".//optionsQuota", "20"))
        currency = root.findtext(".//Currency", DEFAULT_CURRENCY)
        nationality = root.findtext(".//Nationality", DEFAULT_NATIONALITY)
        start_date_str = root.findtext(".//StartDate")
        end_date_str = root.findtext(".//EndDate")
        
        # Validate required parameters
        parameter_element = root.find(".//Configuration/Parameters/Parameter")
        if parameter_element is None:
            raise ValueError("Missing required <Parameter> element")
        
        required_params = ['password', 'username', 'CompanyID']
        for param in required_params:
            if param not in parameter_element.attrib:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Extract and validate Pax data
        rooms = self._parse_rooms(root)
        
        # Validation rules
        self._validate_basic_fields(language, currency, nationality, options_quota)
        start_date, end_date = self._validate_dates(start_date_str, end_date_str)
        
        response_data = {
            "language": language,
            "options_quota": options_quota,
            "currency": currency,
            "nationality": nationality,
            "start_date": start_date,
            "end_date": end_date,
            "ocg": self.var_ocg
        }

        if rooms:
            response_data["rooms"] = rooms
        return response_data

    def _parse_rooms(self, root: ET.Element) -> List[List[Dict[str, Any]]]:
        """Parse and validate room information from XML."""
        rooms = []
        for room in root.findall(".//Paxes"):
            pax_list = []
            child_count = 0
            for pax in room.findall(".//Pax"):
                age = int(pax.get("age", "0"))
                pax_type = "Child" if age <= CHILD_AGE_LIMIT else "Adult"
                pax_list.append({"type": pax_type, "age": age})
                if pax_type == "Child":
                    child_count += 1
            
            self._validate_room(pax_list, child_count)
            rooms.append(pax_list)
        return rooms

    def _validate_room(self, pax_list: List[Dict[str, Any]], child_count: int):
        """Validate room occupancy rules."""
        
        if child_count > ALLOWED_CHILD_COUNT_PER_ROOM:
            raise ValueError("Exceeded maximum allowed children per room")
        if len(pax_list) > ALLOWED_ROOM_GUEST_COUNT:
            raise ValueError("Exceeded maximum allowed guests per room")
        if child_count > 0 and all(p["type"] == "Child" for p in pax_list):
            raise ValueError("A child must have at least one accompanying adult in the same room")

    def _validate_basic_fields(self, language: str, currency: str, nationality: str, options_quota: int):
        """Validate basic request fields."""
        if language not in VALID_LANGUAGES:
            raise ValueError(f"Invalid language: {language}")
        if currency not in VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {currency}")
        if nationality not in VALID_NATIONALITIES:
            raise ValueError(f"Invalid nationality: {nationality}")
        if options_quota > 50:
            raise ValueError("optionsQuota cannot be greater than 50")

    def _validate_dates(self, start_date_str: str, end_date_str: str) -> tuple:
        """Validate date constraints."""
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
        
        if start_date < datetime.today() + timedelta(days=2):
            raise ValueError("StartDate must be at least 2 days from today")
        if (end_date - start_date).days < 3:
            raise ValueError("Stay duration must be at least 3 nights")
            
        return start_date, end_date

    def calculate_selling_price(self, net_price: float, markup: float) -> float:
        """Calculates the selling price by applying markup."""
        return round(net_price + (net_price * (markup / 100)), 2)

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Fetch exchange rate; default to 1.0 if same currency."""
        return EXCHANGE_RATES.get((from_currency, to_currency), 1.0)

    def generate_response(self, parsed_data: Dict[str, Any]) -> str:
        """Generates JSON response based on parsed and calculated values."""
        # Generate a unique ID using timestamp and UUID
        unique_id = f"A#{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        exchange_rate = self.get_exchange_rate("USD", parsed_data["currency"])
        selling_price = self.calculate_selling_price(NET_PRICE, MARKUP_PERCENTAGE) * exchange_rate
        
        response = {
            "id": unique_id,
            "hotelCodeSupplier": "39971881",
            "market": parsed_data["nationality"],
            "price": {
                "minimumSellingPrice": None,
                "currency": parsed_data["currency"],
                "net": NET_PRICE,
                "selling_price": selling_price,
                "selling_currency": parsed_data["currency"],
                "markup": MARKUP_PERCENTAGE,
                "exchange_rate": exchange_rate
            }
        }

        if "rooms" in parsed_data:
            response["rooms"] = parsed_data["rooms"]
        
        return json.dumps([response], indent=2)

    def process_request(self, xml_data: str) -> str:
        """Main function to parse XML, validate, calculate, and return JSON response."""
        try:
            parsed_data = self.parse_xml(xml_data)
            return self.generate_response(parsed_data)
        except Exception as e:
            raise e
        


if __name__ == "__main__":
    # Example usage
    parser = XMLRequestParser()
    
    xml_request = """
    <AvailRQ>
        <source>
            <languageCode>en</languageCode>
        </source>
        <optionsQuota>20</optionsQuota>
        <Configuration>
            <Parameters>
                <Parameter password="XXXXXXXXXX" username="YYYYYYYYY" CompanyID="123456"/>
            </Parameters>
        </Configuration>
        <StartDate>25/02/2025</StartDate>
        <EndDate>28/02/2025</EndDate>
        <Currency>USD</Currency>
        <Nationality>US</Nationality>
        <Paxes>
            <Pax age="4"/>
            <Pax age="30"/>
        </Paxes>
        <Paxes>
            <Pax age="2"/>
            <Pax age="1"/>
            <Pax age="29"/>
        </Paxes>
    </AvailRQ>
    """


    xml_request2 = """
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
    """

    print(parser.process_request(xml_request))




