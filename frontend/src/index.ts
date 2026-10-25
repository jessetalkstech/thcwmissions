import axios from 'axios';

async function splitString(input: string): Promise<string[]> {
    const response = await axios.get(`http://localhost:8000/split_string/${input}`);
    return response.data.result;
}

async function formatDate(input: string): Promise<string> {
    const response = await axios.get(`http://localhost:8000/format_date/${input}`);
    return response.data.result;
}

async function countNumericInGuid(guid: string): Promise<number> {
    const response = await axios.get(`http://localhost:8000/count_numeric_in_guid/${guid}`);
    return response.data.result;
}

// Example usage
(async () => {
    console.log(await splitString("apple,banana,cherry"));
    console.log(await formatDate("2023-10-05"));
    console.log(await countNumericInGuid("123e4567-e89b-12d3-a456-426614174000"));
})();
