from agents.finance import FinanceAgent

finance = FinanceAgent()

print("--- Test 1: Request Invoice ---")
hasil1 = finance.process_finance_request("I agree to the $450 price. Please send me the invoice.")
print(hasil1)

print("\n--- Test 2: Confirm Payment ---")
hasil2 = finance.process_finance_request("I have just transferred the $450 to your bank account.")
print(hasil2)