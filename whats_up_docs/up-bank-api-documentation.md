# Up Bank API Documentation

## Accounts Endpoints

### List Accounts
`GET /accounts`

Retrieve a paginated list of all accounts for the currently authenticated user. The returned list is paginated and can be scrolled by following the prev and next links where present.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page[size]` | integer | The number of records to return in each page.<br>e.g. `?page[size]=30` |
| `filter[accountType]` | string | The type of account for which to return records. This can be used to filter Savers from spending accounts.<br>e.g. `?filter[accountType]=SAVER` |
| `filter[ownershipType]` | string | The account ownership structure for which to return records. This can be used to filter 2Up accounts from Up accounts.<br>e.g. `?filter[ownershipType]=INDIVIDUAL` |

#### Returns

**200 - Successful Response**

| Field | Type | Description |
|-------|------|-------------|
| `data` | Array [AccountResource] | The list of accounts returned in this response. |
| `data[].type` | string | The type of this resource: `accounts` |
| `data[].id` | string | The unique identifier for this account. |
| `data[].attributes.displayName` | string | The name associated with the account in the Up application. |
| `data[].attributes.accountType` | AccountTypeEnum | The bank account type of this account.<br>Possible values: `SAVER`, `TRANSACTIONAL`, `HOME_LOAN` |
| `data[].attributes.ownershipType` | OwnershipTypeEnum | The ownership structure for this account.<br>Possible values: `INDIVIDUAL`, `JOINT` |
| `data[].attributes.balance.currencyCode` | string | The ISO 4217 currency code. |
| `data[].attributes.balance.value` | string | The amount of money, formatted as a string in the relevant currency. For example, for an Australian dollar value of $10.56, this field will be "10.56". The currency symbol is not included in the string. |
| `data[].attributes.balance.valueInBaseUnits` | integer | The amount of money in the smallest denomination for the currency, as a 64-bit integer. For example, for an Australian dollar value of $10.56, this field will be 1056. |
| `data[].attributes.createdAt` | string (date-time) | The date-time at which this account was first opened. |
| `data[].relationships.transactions.links.related` | string (optional) | The link to retrieve the related resource(s) in this relationship. |
| `data[].links.self` | string (optional) | The canonical link to this resource within the API. |
| `links.prev` | string (nullable) | The link to the previous page in the results. If this value is null there is no previous page. |
| `links.next` | string (nullable) | The link to the next page in the results. If this value is null there is no next page. |

### Retrieve Account
`GET /accounts/{id}`

Retrieve a specific account by providing its unique identifier.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The unique identifier for the account.<br>e.g. `2c967f1e-bf1f-4434-a744-64a2d65a19dc` |

#### Returns

**200 - Successful Response**

Response structure is identical to a single account object from the List Accounts endpoint.

## Transactions Endpoints

### List Transactions
`GET /transactions`

Retrieve a list of all transactions across all accounts for the currently authenticated user. The returned list is paginated and can be scrolled by following the next and prev links where present. To narrow the results to a specific date range, pass one or both of `filter[since]` and `filter[until]` in the query string. These filter parameters should not be used for pagination. Results are ordered newest first to oldest last.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page[size]` | integer | The number of records to return in each page.<br>e.g. `?page[size]=30` |
| `filter[status]` | string | The transaction status for which to return records. This can be used to filter HELD transactions from those that are SETTLED.<br>e.g. `?filter[status]=HELD` |
| `filter[since]` | string | The start date-time from which to return records, formatted according to RFC-3339. Not to be used for pagination purposes.<br>e.g. `?filter[since]=2020-01-01T01:02:03+10:00` |
| `filter[until]` | string | The end date-time up to which to return records, formatted according to RFC-3339. Not to be used for pagination purposes.<br>e.g. `?filter[until]=2020-02-01T01:02:03+10:00` |
| `filter[category]` | string | The category identifier for which to filter transactions. Both parent and child categories can be filtered through this parameter. Providing an invalid category identifier results in a 404 response.<br>e.g. `?filter[category]=good-life` |
| `filter[tag]` | string | A transaction tag to filter for which to return records. If the tag does not exist, zero records are returned and a success response is given.<br>e.g. `?filter[tag]=Holiday` |

#### Returns

**200 - Successful Response**

| Field | Type | Description |
|-------|------|-------------|
| `data` | Array [TransactionResource] | The list of transactions returned in this response. |
| `data[].type` | string | The type of this resource: `transactions` |
| `data[].id` | string | The unique identifier for this transaction. |
| `data[].attributes.status` | TransactionStatusEnum | The current processing status of this transaction, according to whether or not this transaction has settled or is still held.<br>Possible values: `HELD`, `SETTLED` |
| `data[].attributes.rawText` | string (nullable) | The original, unprocessed text of the transaction. This is often not a perfect indicator of the actual merchant, but it is useful for reconciliation purposes in some cases. |
| `data[].attributes.description` | string | A short description for this transaction. Usually the merchant name for purchases. |
| `data[].attributes.message` | string (nullable) | Attached message for this transaction, such as a payment message, or a transfer note. |
| `data[].attributes.isCategorizable` | boolean | Boolean flag set to true on transactions that support the use of categories. |
| `data[].attributes.holdInfo` | HoldInfoObject (nullable) | If this transaction is currently in the HELD status, or was ever in the HELD status, the amount and foreignAmount of the transaction while HELD. |
| `data[].attributes.holdInfo.amount` | MoneyObject | The amount of this transaction while in the HELD status, in Australian dollars. |
| `data[].attributes.holdInfo.foreignAmount` | MoneyObject (nullable) | The foreign currency amount of this transaction while in the HELD status. This field will be null for domestic transactions. |
| `data[].attributes.roundUp` | RoundUpObject (nullable) | Details of how this transaction was rounded-up. If no Round Up was applied this field will be null. |
| `data[].attributes.roundUp.amount` | MoneyObject | The total amount of this Round Up, including any boosts, represented as a negative value. |
| `data[].attributes.roundUp.boostPortion` | MoneyObject (nullable) | The portion of the Round Up amount owing to boosted Round Ups, represented as a negative value. If no boost was added to the Round Up this field will be null. |
| `data[].attributes.cashback` | CashbackObject (nullable) | If all or part of this transaction was instantly reimbursed in the form of cashback, details of the reimbursement. |
| `data[].attributes.cashback.description` | string | A brief description of why this cashback was paid. |
| `data[].attributes.cashback.amount` | MoneyObject | The total amount of cashback paid, represented as a positive value. |
| `data[].attributes.amount` | MoneyObject | The amount of this transaction in Australian dollars. For transactions that were once HELD but are now SETTLED, refer to the holdInfo field for the original amount the transaction was HELD at. |
| `data[].attributes.foreignAmount` | MoneyObject (nullable) | The foreign currency amount of this transaction. This field will be null for domestic transactions. |
| `data[].attributes.settledAt` | string (date-time) (nullable) | The date-time at which this transaction settled. This field will be null for transactions that are currently in the HELD status. |
| `data[].attributes.createdAt` | string (date-time) | The date-time at which this transaction was first encountered. |
| `data[].attributes.transactionType` | string (nullable) | A description of the transaction method used e.g. Purchase, BPAY Payment. |
| `data[].attributes.note` | NoteObject (nullable) | A customer provided note about the transaction. Can only be provided by Up High subscribers. |
| `data[].attributes.note.text` | string | A text note about the transaction. |
| `data[].attributes.performingCustomer` | CustomerObject (nullable) | The customer who initiated the transaction. For 2Up accounts this could be the customer who's card was used. |
| `data[].attributes.performingCustomer.displayName` | string | The Upname or preferred name of the customer |
| `data[].attributes.deepLinkURL` | string | A deep link to the transaction receipt screen in-app. |
| `data[].relationships.account.data.type` | string | The type of this resource: `accounts` |
| `data[].relationships.account.data.id` | string | The unique identifier of the resource within its type. |
| `data[].relationships.account.links.related` | string (optional) | The link to retrieve the related resource(s) in this relationship. |
| `data[].relationships.transferAccount` | object | If this transaction is a transfer between accounts, this relationship will contain the account the transaction went to/came from. The amount field can be used to determine the direction of the transfer. |
| `data[].relationships.transferAccount.data` | object (nullable) | The related account data if applicable. |
| `data[].relationships.category` | object | The category relationship information. |
| `data[].relationships.tags` | object | The tags related to this transaction. |
| `data[].relationships.attachment` | object | Any attachment related to this transaction. |
| `links.prev` | string (nullable) | The link to the previous page in the results. If this value is null there is no previous page. |
| `links.next` | string (nullable) | The link to the next page in the results. If this value is null there is no next page. |

## Common Object Models

### MoneyObject

| Field | Type | Description |
|-------|------|-------------|
| `currencyCode` | string | The ISO 4217 currency code. |
| `value` | string | The amount of money, formatted as a string in the relevant currency. For example, for an Australian dollar value of $10.56, this field will be "10.56". |
| `valueInBaseUnits` | integer | The amount of money in the smallest denomination for the currency. For example, for an Australian dollar value of $10.56, this field will be 1056. |

## Enriched Fields

The transaction sync process adds the following enriched fields to transaction data to provide additional context:

### Transaction Enrichments

| Field | Type | Description |
|-------|------|-------------|
| `accountDetails` | object | Additional account information related to the transaction. |
| `accountDetails.displayName` | string | The name associated with the account in the Up application (e.g., "Spending", "Savings"). |
| `accountDetails.accountType` | string | The bank account type (e.g., "TRANSACTIONAL", "SAVER"). |
| `accountDetails.ownershipType` | string | The ownership structure for the account (e.g., "INDIVIDUAL", "JOINT"). |

These enriched fields make it easier to analyze transactions by providing account context without requiring additional lookups. They're particularly valuable when processing transactions from multiple accounts, allowing you to filter or group by account properties.
