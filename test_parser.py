import unittest
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from xml_requests_parser import XMLRequestParser

class TestXMLParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = XMLRequestParser()
        self.valid_xml = '''
        <AvailRQ>
            <timeoutMilliseconds>25000</timeoutMilliseconds>
            <source>
                <languageCode>en</languageCode>
            </source>
            <optionsQuota>20</optionsQuota>
            <Configuration>
                <Parameters>
                    <Parameter password="testpass" username="testuser" CompanyID="123456"/>
                </Parameters>
            </Configuration>
            <SearchType>Multiple</SearchType>
            <StartDate>{start_date}</StartDate>
            <EndDate>{end_date}</EndDate>
            <Currency>USD</Currency>
            <Nationality>US</Nationality>
            <AvailDestinations>
                <Destination>New York</Destination>
                <Destination>Los Angeles</Destination>
            </AvailDestinations>
            <Paxes>
                <Pax age="30"/>
                <Pax age="5"/>
            </Paxes>
        </AvailRQ>
        '''
        self.today = datetime.now()
        self.start_date = (self.today + timedelta(days=3)).strftime('%d/%m/%Y')
        self.end_date = (self.today + timedelta(days=6)).strftime('%d/%m/%Y')
        

    def test_valid_request(self):
        xml = self.valid_xml.format(start_date=self.start_date, end_date=self.end_date)
        result = self.parser.parse_xml(xml)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['nationality'], 'US')
        self.assertEqual(result['options_quota'], 20)

    def test_language_validation(self):
        # Test valid languages
        for lang in ['en', 'fr', 'de', 'es']:
            # Parse the valid XML template
            root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
            
            # Modify the languageCode to the current valid language
            language_element = root.find(".//languageCode")
            language_element.text = lang
            
            # Convert back to XML string
            xml = ET.tostring(root, encoding="unicode")
            
            # Parse and verify the result
            result = self.parser.parse_xml(xml)
            self.assertEqual(result['language'], lang)
        
        # Test invalid language
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        language_element = root.find(".//languageCode")
        language_element.text = "xx"  # Invalid language
        
        # Convert back to XML string
        xml = ET.tostring(root, encoding="unicode")
        
        # Expect a ValueError to be raised
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)

    def test_options_quota(self):
        # Test valid quota
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        options_quota_element = root.find(".//optionsQuota")
        options_quota_element.text = "30"  # Valid quota
        xml = ET.tostring(root, encoding="unicode")
        result = self.parser.parse_xml(xml)
        self.assertEqual(result['options_quota'], 30)
        
        # Test default quota
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        options_quota_element = root.find(".//optionsQuota")
        root.remove(options_quota_element)  # Remove optionsQuota element
        xml = ET.tostring(root, encoding="unicode")
        result = self.parser.parse_xml(xml)
        self.assertEqual(result['options_quota'], 20)  # Should default to 20
        
        # Test quota exceeds maximum
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        options_quota_element = root.find(".//optionsQuota")
        options_quota_element.text = "60"  # Quota exceeds maximum
        xml = ET.tostring(root, encoding="unicode")
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)


    def test_required_parameters(self):
        # Test missing password
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        parameter_element = root.find(".//Parameter")
        del parameter_element.attrib['password']  # Remove password attribute
        xml = ET.tostring(root, encoding="unicode")
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)

    def test_date_validation(self):
        # Test start date too soon
        xml = self.valid_xml.format(
            start_date=self.today.strftime('%d/%m/%Y'),
            end_date=self.end_date
        )        
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)
            
        # Test stay duration too short
        xml = self.valid_xml.format(
            start_date=self.start_date,
            end_date=(self.today + timedelta(days=3)).strftime('%d/%m/%Y')
        )
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)

    def test_currency_validation(self):
        # Test valid currencies
        for currency in ['EUR', 'USD', 'GBP']:
            # Parse the valid XML template
            root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
            
            # Modify the Currency to the current valid currency
            currency_element = root.find(".//Currency")
            currency_element.text = currency
            
            # Convert back to XML string
            xml = ET.tostring(root, encoding="unicode")
            
            # Parse and verify the result
            result = self.parser.parse_xml(xml)
            self.assertEqual(result['currency'], currency)
        
        # Test invalid currency
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        currency_element = root.find(".//Currency")
        currency_element.text = "XYZ"  # Invalid currency
        
        # Convert back to XML string
        xml = ET.tostring(root, encoding="unicode")
        
        # Expect a ValueError to be raised
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)

    def test_passenger_rules(self):
        # Test child without adult
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        paxes = root.find(".//Paxes")
        paxes.clear()  # Remove existing Pax elements
        ET.SubElement(paxes, "Pax", {"age": "4"})  # Add a child without an adult
        xml = ET.tostring(root, encoding="unicode")
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)
            
        # Test too many children
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        paxes = root.find(".//Paxes")
        paxes.clear() 
        for age in [3,4,5,25]:  # Add too many children
            ET.SubElement(paxes, "Pax", {"age": str(age)})
        xml = ET.tostring(root, encoding="unicode")
        with self.assertRaises(ValueError):
            self.parser.parse_xml(xml)

    def test_price_calculations(self):
        xml = self.valid_xml.format(start_date=self.start_date, end_date=self.end_date)
        response = self.parser.process_request(xml)
        self.assertIn('selling_price', response)
        self.assertIn('markup', response)
        self.assertIn('exchange_rate', response)
        self.assertIn('selling_currency', response)

    def test_child_count_validation(self):
        # Parse the valid XML template
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        
        # Find the Paxes element and modify it
        paxes = root.find(".//Paxes")
        paxes.clear()  # Remove existing Pax elements
        
        # Add more children than allowed
        for age in [3, 4, 5, 25]:  # 3 children
            ET.SubElement(paxes, "Pax", {"age": str(age)})
        
        # Convert back to XML string
        xml = ET.tostring(root, encoding="unicode")
        
        # Expect a ValueError to be raised
        with self.assertRaises(ValueError) as context:
            self.parser.parse_xml(xml)
        
        # Verify the error message
        self.assertEqual(str(context.exception), "Exceeded maximum allowed children per room")

    def test_guest_count_validation(self):
        # Parse the valid XML template
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        
        # Find the Paxes element and modify it
        paxes = root.find(".//Paxes")
        paxes.clear()  # Remove existing Pax elements
        
        # Add more guests than allowed
        for age in [30, 25, 20, 15, 10]:  # 5 guests
            ET.SubElement(paxes, "Pax", {"age": str(age)})
        
        # Convert back to XML string
        xml = ET.tostring(root, encoding="unicode")
        
        # Expect a ValueError to be raised
        with self.assertRaises(ValueError) as context:
            self.parser.parse_xml(xml)
        
        # Verify the error message
        self.assertEqual(str(context.exception), "Exceeded maximum allowed guests per room")

    def test_nationality_validation(self):
        # Parse the valid XML template
        root = ET.fromstring(self.valid_xml.format(start_date=self.start_date, end_date=self.end_date))
        
        # Modify the Nationality to an invalid value
        nationality_element = root.find(".//Nationality")
        nationality_element.text = "XX"  # Invalid nationality
        
        # Convert back to XML string
        xml = ET.tostring(root, encoding="unicode")
        
        # Expect a ValueError to be raised
        with self.assertRaises(ValueError) as context:
            self.parser.parse_xml(xml)
        
        # Verify the error message
        self.assertEqual(str(context.exception), "Invalid nationality: XX")

if __name__ == '__main__':
    unittest.main() 