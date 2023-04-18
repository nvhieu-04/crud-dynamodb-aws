# CRUD DynamoDB AWS Lambda API Gateway

This is a sample project that demonstrates how to create a CRUD (Create, Read, Update, Delete) API using AWS Lambda and API Gateway with DynamoDB as the backend database. This project provides boilerplate code for creating and deploying the API as well as instructions for testing it.

## Getting Started

To get started with this project, you will need to have an AWS account and the AWS CLI installed on your local machine. You should also have Python 3 and pip installed.

1. Clone this repository to your local machine: git clone https://github.com/nvhieu-04/crud-dynamodb-aws.git
2. Navigate to the project directory: cd crud-dynamodb-aws
3. Install the project dependencies: pip install -r requirements.txt
4. Create a new DynamoDB table with the name "users" and a partition key of "id".
5. Modify the config.py file with your AWS credentials and the name of your DynamoDB table.
6. Deploy the API to AWS Lambda and API Gateway: ./deploy.sh
7. Test the API using a tool like Postman or the AWS API Gateway console.

## Usage

This API provides the following endpoints:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/users` | GET | Get all users |
| `/users/{userId}` | GET | Get a specific user by ID |
| `/users` | POST | Create a new user |
| `/users/{userId}` | PUT | Update an existing user |
| `/users/{userId}` | DELETE | Delete a user |

### Example Request and Response


## Contributing

If you find a bug or have an idea for a new feature, feel free to open an issue or submit a pull request. Contributions are always welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
