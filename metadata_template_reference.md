ID: 72673c55-431d-431c-835d-cc97f866638d
Type: metadata_template
Template Key: financialDocumentBase
Scope: enterprise_218068865
Display Name: FinancialDocumentBase
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: c8d1dfe0-673e-4dd0-bf73-651b0064f106
        Type: enum
        Key: documentType
        Display Name: document_type
        Hidden: false
        Options:
            -
                ID: 96f66010-6f51-4985-88df-c1a3609e3393
                Key: '1099'
            -
                ID: b793a7d0-05b9-4992-b98e-fde6eb314018
                Key: W-2
            -
                ID: 14d6bc0e-9de0-4491-9040-8f2c8cd09b04
                Key: Account Statement
            -
                ID: 14f1fe5a-a61f-42c8-90a5-4720e3d2af37
                Key: Mortgage Statement
            -
                ID: e8c100bc-0cd5-4655-baff-bd888242610d
                Key: Trust Document
            -
                ID: 7faae7b2-d3c0-4b51-bf5d-1b0763da5b08
                Key: Asset List
            -
                ID: f2ebb3ea-af08-4ed9-9e54-18e2ce8c0330
                Key: '1040'
            -
                ID: 8949ac3f-13f3-426c-b6cd-9de0bf14507b
                Key: Personal Financial Statement
            -
                ID: 2105751e-2d9e-4020-a2ad-a0ad7ec4e72f
                Key: Life Insurance Document
            -
                ID: e0fe5807-c728-4ed8-aa77-193c81673479
                Key: Other
    -
        ID: d54101d1-fe5b-4950-9174-ff8a97e286cf
        Type: date
        Key: taxYear
        Display Name: tax_year
        Hidden: false
    -
        ID: 545585fd-b1c2-4cc1-9f21-4182a4ade3a4
        Type: string
        Key: issuerName
        Display Name: issuer_name
        Hidden: false
    -
        ID: 5dd1bd60-0bad-469b-b117-1d6023eb2c33
        Type: string
        Key: recipientName
        Display Name: recipient_name
        Hidden: false
    -
        ID: b2b2159b-375d-4adc-a716-e59f92805e37
        Type: date
        Key: documentDate
        Display Name: document_date
        Hidden: false
    -
        ID: 2f237571-6047-49cd-a3d4-08820e6fa7b3
        Type: string
        Key: accountOrPolicyNoMasked
        Display Name: account_or_policy_no_masked
        Hidden: false
    -
        ID: d2938d02-fe2d-4e67-81e4-c40ede96be94
        Type: enum
        Key: isLegible
        Display Name: is_legible
        Hidden: false
        Options:
            -
                ID: 95af85ac-fbea-4197-a887-ea1ff92ac218
                Key: 'Yes'
            -
                ID: 3fe834ea-ca3f-4e6f-9751-7745df91b78d
                Key: 'No'



ID: 4efcdd51-b298-4bb6-bea4-4fe435c0270e
Type: metadata_template
Template Key: irs1099
Scope: enterprise_218068865
Display Name: IRS1099
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 28196804-448d-4017-8536-1530beead443
        Type: enum
        Key: formVariant
        Display Name: form_variant
        Hidden: false
        Options:
            -
                ID: e297b031-666c-418a-b363-0dd64dc0e760
                Key: INT
            -
                ID: c7d3c9ea-b3c9-4fdf-a860-8437ee0a0f67
                Key: DIV
            -
                ID: c5020441-73d6-4b1b-acbd-92f8b55b5c80
                Key: B
            -
                ID: 498857bb-f21f-4376-96b4-61886a8e6474
                Key: MISC
            -
                ID: bc6d0c35-6c83-46c5-a504-98f0eacfbb35
                Key: NEC
    -
        ID: 285eceaf-259d-4d15-b1d0-b5a8314ccecd
        Type: string
        Key: payerTinMasked
        Display Name: payer_tin_masked
        Hidden: false
    -
        ID: 57df9451-43c1-4e0b-8ac9-67602598e62d
        Type: string
        Key: recipientTinMasked
        Display Name: recipient_tin_masked
        Hidden: false
    -
        ID: cccb9846-70ea-4b7a-bc31-89efc65ca80e
        Type: float
        Key: box1IncomeAmount
        Display Name: box1_income_amount
        Hidden: false
    -
        ID: c3936047-9540-4af4-8116-f5c60436e5ee
        Type: float
        Key: federalTaxWithheld
        Display Name: federal_tax_withheld
        Hidden: false
    -
        ID: b1482bf9-608f-4b08-aa3c-9da73874f5da
        Type: float
        Key: stateTaxWithheld
        Display Name: state_tax_withheld
        Hidden: false
    -
        ID: 4bed5511-6ab3-47ef-afe6-0284b20dbf3b
        Type: float
        Key: costBasis
        Display Name: cost_basis
        Hidden: false
    -
        ID: 1b6b7f46-c22b-4731-9670-760d5ff3cf2e
        Type: date
        Key: dateSold
        Display Name: date_sold
        Hidden: false



ID: 5a888ca3-731c-44f8-b34c-c0cf69d99670
Type: metadata_template
Template Key: irsw2
Scope: enterprise_218068865
Display Name: IRSW2
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 109f151e-183f-4d17-9bb2-d8339e325ec0
        Type: string
        Key: employerEinMasked
        Display Name: employer_ein_masked
        Hidden: false
    -
        ID: 4bfff117-d278-4029-b38e-f75a8ecaf40e
        Type: string
        Key: employeeSsnMasked
        Display Name: employee_ssn_masked
        Hidden: false
    -
        ID: a1d8a5db-e8ad-43b1-b76a-bac8ed78dd03
        Type: float
        Key: box1Wages
        Display Name: box1_wages
        Hidden: false
    -
        ID: 233582d9-4d62-4607-81e1-815718f27797
        Type: float
        Key: box2FederalWithholding
        Display Name: box2_federal_withholding
        Hidden: false
    -
        ID: 46c6acab-ed34-4c9a-82e2-3c53cafe2f16
        Type: string
        Key: box12Codes
        Display Name: box12_codes
        Hidden: false
    -
        ID: 5c9957a5-aa8a-484d-b471-ac7ebe517001
        Type: float
        Key: stateWages
        Display Name: state_wages
        Hidden: false
    -
        ID: ed7ab2ad-14e7-4c04-8e45-fb032525a2ef
        Type: float
        Key: localWages
        Display Name: local_wages
        Hidden: false



ID: 04018d27-2c3e-4a58-a74d-0e525bb92c10
Type: metadata_template
Template Key: accountStatement
Scope: enterprise_218068865
Display Name: AccountStatement
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 48ec7bc7-64ae-4f45-b4fa-e2176e060668
        Type: string
        Key: institutionName
        Display Name: institution_name
        Hidden: false
    -
        ID: 57920e91-0e59-404b-b92d-3669305c6928
        Type: enum
        Key: accountType
        Display Name: account_type
        Hidden: false
        Options:
            -
                ID: 6be8bd87-75c8-4c7f-a7b2-07b7bd040492
                Key: Checking
            -
                ID: 9c9a4fca-e4f3-4729-ac74-2c8b7a820087
                Key: Savings
            -
                ID: 9499c57c-cde7-4e0e-9b76-66db84b548d1
                Key: Brokerage
            -
                ID: 20f52274-e5e8-4581-aea3-f29c3f48af3f
                Key: Retirement
            -
                ID: 7e51d4e2-5d96-4d2b-bd51-d2f325d2f002
                Key: Credit
    -
        ID: ff3699e9-00f0-44c2-a223-d69632bd56c6
        Type: date
        Key: statementPeriodStart
        Display Name: statement_period_start
        Hidden: false
    -
        ID: b61eaf43-8868-4407-8184-f827f073aa17
        Type: date
        Key: statementPeriodEnd
        Display Name: statement_period_end
        Hidden: false
    -
        ID: e056215c-a076-43af-9679-8a9eaf042851
        Type: float
        Key: beginningBalance
        Display Name: beginning_balance
        Hidden: false
    -
        ID: 3d1bf46b-88f2-40dc-8d50-2575ad4e60f1
        Type: float
        Key: endingBalance
        Display Name: ending_balance
        Hidden: false
    -
        ID: 8171123c-57bb-47ce-bdad-286fe804a715
        Type: float
        Key: totalDeposits
        Display Name: total_deposits
        Hidden: false
    -
        ID: 90e13dda-aa2f-4a8d-aa0f-94f01f7c8a3a
        Type: float
        Key: totalWithdrawals
        Display Name: total_withdrawals
        Hidden: false
    -
        ID: 44749d3f-0908-44e1-93d5-8d9e1c0c9e05
        Type: float
        Key: netChange
        Display Name: net_change
        Hidden: false



ID: 401875af-f3e0-49c2-931d-f45c1377f973
Type: metadata_template
Template Key: mortgageStatement
Scope: enterprise_218068865
Display Name: MortgageStatement
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 0dd63224-d747-4040-b1e2-5acca260d807
        Type: string
        Key: lenderName
        Display Name: lender_name
        Hidden: false
    -
        ID: 1978b436-73a0-4ce5-aa22-e34a6c56ae94
        Type: string
        Key: loanNumberMasked
        Display Name: loan_number_masked
        Hidden: false
    -
        ID: 980b5c50-f56a-478e-b9eb-541524cfd1d6
        Type: float
        Key: principalBalance
        Display Name: principal_balance
        Hidden: false
    -
        ID: 561bb633-2ae1-4108-9a18-71eb818d64e9
        Type: float
        Key: interestRate
        Display Name: interest_rate
        Hidden: false
    -
        ID: 1e94ead1-cb92-440a-aaeb-00ecced4ec29
        Type: float
        Key: monthlyPaymentAmount
        Display Name: monthly_payment_amount
        Hidden: false
    -
        ID: fea63d8f-0997-49c3-bd6e-fe3f0f45ef0c
        Type: date
        Key: nextPaymentDue
        Display Name: next_payment_due
        Hidden: false
    -
        ID: a76d7ac7-9c2d-4af8-9f4f-fc82ea0ea9fe
        Type: float
        Key: escrowBalance
        Display Name: escrow_balance
        Hidden: false
    -
        ID: 0efc2491-d9d0-40c4-9e99-3f9d6ec5ab0c
        Type: float
        Key: amountPastDue
        Display Name: amount_past_due
        Hidden: false
    -
        ID: d5d67d42-6007-41ca-a04c-376e0e481ff0
        Type: string
        Key: propertyAddress
        Display Name: property_address
        Hidden: false




ID: 4d8a7769-f0e6-42b6-bf7d-69179dea4243
Type: metadata_template
Template Key: trustDocument
Scope: enterprise_218068865
Display Name: TrustDocument
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 4c251527-fe20-47c3-84a4-44ae02a30e05
        Type: string
        Key: trustName
        Display Name: trust_name
        Hidden: false
    -
        ID: dcd9185b-356a-49d7-a98e-0b2e4ecf90ad
        Type: enum
        Key: trustType
        Display Name: trust_type
        Hidden: false
        Options:
            -
                ID: 40e2dab0-6f7c-491f-a14f-75eb4b2bf4cd
                Key: Revocable
            -
                ID: 8c4377c4-f50e-4753-90c2-2f6704d81385
                Key: Irrevocable
            -
                ID: a77609dd-b59e-4fbd-becd-e3c27d28cdcb
                Key: Land
            -
                ID: f9f5f0ba-5e0e-46f1-b8a5-bb87c5fac0c5
                Key: Other
    -
        ID: 9808a346-9c7a-4e87-99b9-137ae5947aa3
        Type: date
        Key: dateOfTrust
        Display Name: date_of_trust
        Hidden: false
    -
        ID: c2c60817-35b1-4a95-b105-923a12e553fc
        Type: string
        Key: grantorNames
        Display Name: grantor_names
        Hidden: false
    -
        ID: e862674b-2ad1-4c78-9854-9853abfc8a92
        Type: string
        Key: trusteeNames
        Display Name: trustee_names
        Hidden: false
    -
        ID: ee38412f-4010-4640-b006-9deeac5dc996
        Type: string
        Key: beneficiaryNames
        Display Name: beneficiary_names
        Hidden: false
    -
        ID: 46604598-16b4-46a7-bb5f-0208fddb977d
        Type: string
        Key: governingState
        Display Name: governing_state
        Hidden: false
    -
        ID: 896ed91f-e047-44a2-a5fa-81be0c136094
        Type: string
        Key: einMasked
        Display Name: ein_masked
        Hidden: false



ID: d0bbd9d2-12d4-4ae1-8728-854c387e41e0
Type: metadata_template
Template Key: assetList
Scope: enterprise_218068865
Display Name: AssetList
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: b497f46d-d377-4a39-bdc6-4bd56aff8c9f
        Type: enum
        Key: assetCategory
        Display Name: asset_category
        Hidden: false
        Options:
            -
                ID: 1d6446af-86ba-47ce-b765-d786d0e1dda1
                Key: Real Estate
            -
                ID: 92c4b13f-369a-45e4-8b3e-51fd93a8da17
                Key: Vehicle
            -
                ID: 55bfa949-4408-4115-a0fe-7166861bae31
                Key: Securities
            -
                ID: 3977e220-7027-44a0-ab53-b5fe48cdca0e
                Key: Cash
            -
                ID: 628f39bf-c16d-4cea-b170-6306e632d9f0
                Key: Other
    -
        ID: 6e686a81-a4f9-4594-8c20-f8b1651d2de3
        Type: string
        Key: assetDescription
        Display Name: asset_description
        Hidden: false
    -
        ID: 11953248-a772-4547-b1d9-5be4bf482960
        Type: float
        Key: quantity
        Display Name: quantity
        Hidden: false
    -
        ID: 52acb4e4-01ad-4691-8b7d-ef247b251cb9
        Type: float
        Key: costBasis
        Display Name: cost_basis
        Hidden: false
    -
        ID: e43ad2e7-cadc-47aa-9a72-47eb021e5963
        Type: float
        Key: currentValue
        Display Name: current_value
        Hidden: false
    -
        ID: 2299cad2-594e-4e06-b7f5-921cf497f8cd
        Type: date
        Key: valuationDate
        Display Name: valuation_date
        Hidden: false
    -
        ID: adf4b570-7a83-4f38-9f58-ce1f79504986
        Type: string
        Key: ownerNames
        Display Name: owner_names
        Hidden: false
    -
        ID: d8a8b09e-a095-4a00-8cc8-7f41c556afc8
        Type: string
        Key: locationOrAccount
        Display Name: location_or_account
        Hidden: false



ID: da78e89a-5cfa-496a-9248-835b9a98bd71
Type: metadata_template
Template Key: irs1040
Scope: enterprise_218068865
Display Name: IRS1040
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: da8e736f-674b-4f33-a311-a2be702b785f
        Type: enum
        Key: filingStatus
        Display Name: filing_status
        Hidden: false
        Options:
            -
                ID: 41f06944-c15b-4b2b-ad91-d739a834ca88
                Key: Single
            -
                ID: 79e1cc7a-0cc7-48b9-af3f-8b339fa77484
                Key: Married Filing Jointly
            -
                ID: c5de9b5a-c8a8-4d54-ae65-533b97bf7747
                Key: Married Filing Separately
            -
                ID: a3262ef4-9a64-44c2-8a74-0dfe39adc22e
                Key: Head of Household
            -
                ID: 1e316e57-aefd-4173-a93a-7dbca1172151
                Key: Qualifying Surviving Spouse
    -
        ID: 3c1a5b43-e879-446f-8658-e90810c177d0
        Type: float
        Key: agi
        Display Name: agi
        Hidden: false
    -
        ID: 61a10d47-543a-4496-8170-eb2bbda227b8
        Type: float
        Key: taxableIncome
        Display Name: taxable_income
        Hidden: false
    -
        ID: 043c03c2-61a2-4317-9d68-4cae9b02feb4
        Type: float
        Key: totalTax
        Display Name: total_tax
        Hidden: false
    -
        ID: 0ccac494-adbf-4f36-9b43-119239a45477
        Type: float
        Key: totalPayments
        Display Name: total_payments
        Hidden: false
    -
        ID: b4e95b85-13c4-47d6-a8a4-e7d88f2cfcfa
        Type: float
        Key: refundAmount
        Display Name: refund_amount
        Hidden: false
    -
        ID: 725b6d43-1370-4a7f-9be8-d8e95daa2d37
        Type: float
        Key: amountOwed
        Display Name: amount_owed
        Hidden: false
    -
        ID: 560cdbce-483e-4f12-962a-81a9412a491c
        Type: string
        Key: taxpayerSsnMasked
        Display Name: taxpayer_ssn_masked
        Hidden: false
    -
        ID: 659eb6e9-fba3-446d-837e-1e05f5c775cb
        Type: string
        Key: spouseSsnMasked
        Display Name: spouse_ssn_masked
        Hidden: false



ID: fe141f5e-5050-4fc3-b6e1-ff133bb9190d
Type: metadata_template
Template Key: personalFinancialStatement
Scope: enterprise_218068865
Display Name: PersonalFinancialStatement
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 67e7e0dd-31f9-4d8b-904b-fc27b3cdb8e0
        Type: date
        Key: statementDate
        Display Name: statement_date
        Hidden: false
    -
        ID: 739ea7f8-02eb-4e87-8ac9-35360e1ed1c1
        Type: float
        Key: totalAssets
        Display Name: total_assets
        Hidden: false
    -
        ID: 7b8ff0b2-f223-426c-ac2f-e201c7d245e1
        Type: float
        Key: totalLiabilities
        Display Name: total_liabilities
        Hidden: false
    -
        ID: 8c5af56b-b642-4966-b2aa-a2e9b26780e3
        Type: float
        Key: netWorth
        Display Name: net_worth
        Hidden: false
    -
        ID: ae77ba34-baac-459c-acba-df74beab94fc
        Type: float
        Key: annualIncome
        Display Name: annual_income
        Hidden: false
    -
        ID: f368a0a5-27cf-4937-b2a6-b1cd32fe9eb7
        Type: float
        Key: annualExpenses
        Display Name: annual_expenses
        Hidden: false
    -
        ID: 1693a76c-9998-4c72-a1ac-4575c630ca86
        Type: float
        Key: contingentLiabilities
        Display Name: contingent_liabilities
        Hidden: false

        

ID: ef015a09-5185-4d3b-ad62-59746baa5d5e
Type: metadata_template
Template Key: lifeInsurancePolicy
Scope: enterprise_218068865
Display Name: LifeInsurancePolicy
Hidden: false
Copy Instance On Item Copy: false
Fields:
    -
        ID: 25c79ee5-75c3-4132-9725-90e1dc5ac124
        Type: string
        Key: policyNumberMasked
        Display Name: policy_number_masked
        Hidden: false
    -
        ID: 9d6af3ad-b682-4108-b7df-590ef2401d82
        Type: enum
        Key: policyType
        Display Name: policy_type
        Hidden: false
        Options:
            -
                ID: 0ce819e4-9aed-4a29-959c-8daf13de3f06
                Key: Term
            -
                ID: 806c25f6-2b98-4f4c-892d-0a43b5099c0d
                Key: Whole
            -
                ID: ab0ffc02-33ef-4dd7-8059-8c9a3d304626
                Key: Universal
            -
                ID: 1b718ebe-a770-49bc-97ac-d5a039bc75e3
                Key: Variable
            -
                ID: 22570417-2cf5-44ae-a2d8-078db18cd617
                Key: Variable Universal
            -
                ID: 8b9c4913-5181-49da-89ac-35f753c890cc
                Key: Indexed Universal
    -
        ID: 4ba91ef6-deba-4292-81d8-5826995f923e
        Type: float
        Key: faceAmount
        Display Name: face_amount
        Hidden: false
    -
        ID: 28e7608f-d7aa-49f3-9b72-ff3904734941
        Type: float
        Key: cashValue
        Display Name: cash_value
        Hidden: false
    -
        ID: 653baeef-a9e3-4834-b9f1-1b4894f275ec
        Type: date
        Key: issueDate
        Display Name: issue_date
        Hidden: false
    -
        ID: 6cc39bea-2436-4a6e-8e31-6e235ec61c07
        Type: float
        Key: premiumAmount
        Display Name: premium_amount
        Hidden: false
    -
        ID: 66f0e309-74d2-48a3-a13b-9f7509238537
        Type: enum
        Key: premiumMode
        Display Name: premium_mode
        Hidden: false
        Options:
            -
                ID: 54ebdf97-9357-45bf-a8cb-1c6b391cd4f1
                Key: Monthly
            -
                ID: cc9ce7fd-ac3a-4c38-b205-938baedcd421
                Key: Quarterly
            -
                ID: dc91c4f8-8dc3-4093-8dde-44c2e5a72aa4
                Key: Semi-Annual
            -
                ID: 0ec3309a-0999-41ad-b8ad-af8fa9b899ca
                Key: Annual
    -
        ID: 9390325e-6a84-41ff-81da-dafe8d859d94
        Type: string
        Key: insuredName
        Display Name: insured_name
        Hidden: false
    -
        ID: cbcdfab5-ac24-4165-86f1-cef529c3bc91
        Type: string
        Key: ownerName
        Display Name: owner_name
        Hidden: false
    -
        ID: 43441543-40c1-4897-b993-0db1a6c6eeaa
        Type: string
        Key: primaryBeneficiary
        Display Name: primary_beneficiary
        Hidden: false
    -
        ID: 06cd1ee1-36c4-4b22-9200-c47fe76ed3c5
        Type: enum
        Key: policyStatus
        Display Name: policy_status
        Hidden: false
        Options:
            -
                ID: 890dd47c-7881-4f58-8fb8-560510774949
                Key: In-Force
            -
                ID: 9b96f1c1-4532-4935-84c0-a8f91281b22e
                Key: Lapsed
            -
                ID: e279eb5f-5522-4280-bea0-0b7c29ed46f3
                Key: Pending
            -
                ID: 62676932-e41c-40b0-8d42-3df93e631bb1
                Key: Canceled
