from client import Client
import asyncio
import os
import dotenv

dotenv.load_dotenv()

async def main():
    # initiate client without async context manager and log in
    # client = Client(os.getenv("COMMBANK_USERNAME"), os.getenv("COMMBANK_PASSWORD"))
    # await client._login()
    # Client must be closed manually to avoid resource leak
    # await client.close()

    # Initiate client with async context manager and log in (recommended)
    async with Client(os.getenv("COMMBANK_USERNAME"), os.getenv("COMMBANK_PASSWORD")) as client:
        # get account ID
        account_id = (await client.get_accounts())[0]["id"]

        # get transactions (first page)
        transactions = await client.get_transactions(account_id)

        # get transactions (second page)
        transactions2 = await client.get_transactions(account_id, page=2)

        # print transactions
        print(transactions)
        print(transactions2)

asyncio.run(main())