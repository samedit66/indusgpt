from src import types


INTRODUCTION = """
Hi brother!  
Thanks for reaching out 🙏  

We work with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.  
We are looking to buy or rent corporate accounts in India that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.  
We are ready for long-term cooperation and offer up to 5% of the profit for stable account performance.  
For example: ₹500,000 daily volume = ₹25,000 your share (5%).
Let's build a strong and profitable partnership 💪

I’m a bit tied up at the moment, so my response may not be immediate—thanks for your patience!
"""

QUESTIONS = [
    types.Question(
        text="Do you have corporate (business) accounts? In which banks?",
        answer_requirement=(
            "User MUST agree that they HAVE A CORPORATE/BUSINESS bank account and TELL THE BANK NAME.\n"
            "Users usually do not explicitly tell 'I have a corporate account', but say things like 'Yes' and the bank name.\n"
            "If user says that they have SAVINGS or CURRENT answer is INVALID!\n"
            "Other types of accounts are invalid:\n"
            "If user says that they have current account, or personal account, "
            "or savings account that means they DO NOT HAVE CORPORATE ACCOUNT - that's invalid.\n\n"
            "**Pay attention to the following rules**:\n"
            "- CURRENT ACCOUNT IS NOT CORPORATE/BUSINESS ACCOUNT\n"
            "- PERSONAL ACCOUNT IS NOT CORPORATE/BUSINESS ACCOUNT\n"
            "- SAVINGS ACCOUNT IS NOT CORPORATE/BUSINESS ACCOUNT\n\n"
            "**POPULAR SHORTCUTS OF BANK NAMES:L**\n"
            "- BOB means Bank of Boroda\n"
            "- PNB means Punjab National Bank\n"
            "- IPPB means Indian post payment bank\n"
            "- IDFC (or idfc) means IDFC First Bank\n"
            "\n"
            "Valid examples:\n"
            "- BANK OF MAHARASTRA yes\n"
            "- Yes City union bank\n"
            "- Yes corporate account in ICICI\n"
            "- I have a corporate account in Sber bank.\n"
            "- I got a business account in Bank of Baroda.\n"
            "- Yes, I have a corporate account in ICICI.\n"
            "- Yes SBI\n"
            "- SBI yes\n"
            "- State bank yes bisuness account\n"
            "- Yes In IPPB\n"
            "- Yes it is a corporate bank Indian post payment bank\n"
            "- Yes I do. In IndusInd bank\n"
            "- Yes, I have a Business account at  SBI\n"
            "- I have Federal Bank and Induslnd Bank Federal E-biz corporate\n"
            "- Yes in Airtel payment bank\n"
            "\n"
            "Invalid examples:\n"
            "- Yes i have an Axis Bank current account (user mentions having current account - so it's invalid)"
            "- I don't have corporate\n"
            "- No corporate\n"
            "- I have a personal account in ICICI.\n"
            "- I have savings account in SBI.\n"
            "- I have current account with QR.\n"
            "- Only saving account\n"
            "- Current only IOB\n"
            "- Kotak Mahindra bank\n"
            "- SBI No I don't have business account\n"
            "- Saving account\n"
            "- Canara Current account\n"
            "- I do not have any corporate account my savings account\n"
            "- Saving accounts Punjab National bank Current account Yes (user mentioned that they have current account - it's invalid)\n"
        ),
    ),
    types.Question(
        text="Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?",
        answer_requirement=(
            "User response **must** confirm they have a connected PSP and include the PSP name.\n"
            "Known PSP names: Razorpay, Cashfree, PayU, Getepay, Paytm.\n"
            "If user mentions other PSP names, their answer must confirm they really have that PSP.\n"
            "If user says they don't have a PSP or it's not connected, the answer is invalid.\n"
            "Valid examples:\n"
            "- Yes, I have linked with Razorpay\n"
            "- Yes, I have Razorpay connected.\n"
            "- My account is integrated with PayU.\n"
            "- We use Cashfree for payments.\n"
            "- Razorpay is connected.\n",
            "- PayU.\n",
            "- Yes, I have a Amazon PSP (This PSP is not listed above, but user confirms they really have it).\n",
            "Invalid examples:\n"
            "- I don't have a PSP.\n"
            "- No, I don't have a PSP.\n"
            "- No.",
        ),
    ),
    types.Question(
        text="Can you provide login and password access to the PSP account?",
        answer_requirement=(
            "User response **must** provide actual login credentials (login and password) or confirm and commit to "
            "providing them. Any response indicating inability or unwillingness to share credentials is invalid.\n"
            "User MUST provide LOGIN and PASSWORD to have a valid answer.\n"
            "Examples of valid responses:\n"
            "- Login admin123, password test456\n"
            "- Username is merchant_1, pass is secure123, API key is abcd1234\n"
            "- Yes, I'll share them right now - login: mystore, password: shop2023\n"
            "- Of course, the credentials are: user=admin pass=12345\n\n"
            "- Corporate ID- BALA8840\nC- User ID-GAURA670\nLogin password - R&2133\nTransaction password - G&8987\n"
            "- Credential at Cashfree\nUsername: xyzchakma1@gmail.com\nPassword: Admin@8729\n"
            "Examples of invalid responses:\n"
            "- I'll check with my team first\n"
            "- I need to think about it\n"
            "- I don't have access right now\n"
            "- Let me get back to you on this\n"
            "- I can't share these details"
            "- Yeah.\n"
            "- Yes.\n"
            "- Yes, I'll share them right now.\n"
        ),
    ),
    types.Question(
        text="Please provide the details of the company linked to your payment-gateway account:\n"
        "- Company Name\n"
        "- Registered Address\n"
        "- Contact Phone Number\n"
        "- Email Address",
        answer_requirement=(
            "User response **must** include all four items: company name, address, phone number, and email.\n\n"
            "Examples of valid responses:\n"
            "- Acme Corp, 123 Main St, Springfield, +1-555-1234, info@acme.com\n"
            "- Company Name: Widget Co.; Address: 456 Elm Rd, Metropolis; Phone: +44-20-7946-0958; Email: support@widget.co.uk\n\n"
            "- Company name: Online Services\nRegistered address: 63, Borapansury-II, Mizoram, India\nContact phone number: 8729873085\nEmail: xyzchakma1@gmail.com\n"
            "Examples of invalid responses:\n"
            "- Just Acme Corp and its address\n"
            "- I'll send it later\n"
            "- Only phone number provided\n"
        ),
    ),
    types.Question(
        text="Please describe your company's business activities and what products/services you plan to sell",
        answer_requirement=(
            "User response **must** describe their company's business activities or what products/services they plan to sell.\n"
            "The provided description may be not detailed, but clearly tells the business activity\n\n"
            "Examples of valid responses:\n"
            "- Food business\n"
            "- Fast food cart"
            "- We sell electronics like smartphones and laptops\n"
            "- Our company provides IT consulting services\n"
            "- We're an online clothing store selling fashion accessories\n"
            "- We sell digital products like software licenses\n\n"
            "- Online Services is a online selling platform for digital products\n"
            "Examples of invalid responses:\n"
            "- We're a company\n"
            "- Not sure yet\n"
            "- Will decide later\n"
        ),
    ),
    types.Question(
        text=(
            "Do you already have a website approved by the PSP?\n"
            "If yes — please give us hosting access (we may need to adjust code or API)\n"
            "If not — we will create the website ourselves"
        ),
        answer_requirement=(
            "User response **must** clearly indicate if they have a website. If they have one, they **must** "
            "provide hosting access details (credentials, URL, etc). If they don't have a website or are unsure, "
            "that's perfectly fine.\n\n"
            "Examples of valid responses:\n"
            "- No...\n"
            "- No, I don't have a website yet\n"
            "- Not sure, we're still working on it\n"
            "- Yes, here's the hosting access - username: admin, password: secure123\n"
            "- Yes, you can access it at mysite.com/admin with login: merchant, pass: shop2023\n"
            "- Yes, FTP details are host: ftp.mysite.com, user: ftpuser, pass: ftppass123\n\n"
            "- but I don't have a website\n"
            "- I don't have a website or Hosting right now\n"
            "Examples of invalid responses:\n"
            "- Yes (without providing access details)\n"
            "- I have a website but can't share access now\n"
            "- Maybe\n"
            "- I'll think about giving access\n"
            "- The website is www.mysite.com (but no access details)"
        ),
    ),
    types.Question(
        text="Are you open to working under a profit-sharing model (5% of transaction volume) instead of a one-time deal?",
        answer_requirement=(
            "User response **must** clearly indicate agreement to the profit-sharing model.\n"
            "Agreemnt to one time deal or disagreemnet at all is INVALID answer!\n\n"
            "Examples of valid responses:\n"
            "- Yes, I agree to 5% profit sharing\n"
            "- Of course.\n"
            "- Sure.\n"
            "- Sure, I agree to 5% profit sharing\n"
            "- Sure!\n"
            "- Sure, that works for me\n"
            "- I accept those terms\n"
            "- Absolutely, let's do profit sharing\n\n"
            "- I agree.\n"
            "- Okay sir\n"
            "- yes I am ready to work with 5% of the transaction volume\n"
            "- Yes\n"
            "Examples of invalid responses:\n"
            "- No\n"
            "- Maybe later\n"
            "- Need to think about it\n"
            "- What about 3%?\n"
            "- Let me check with my team\n"
            "- I prefer fixed price\n"
            "- I'm not sure about that\n"
            "- One time deal how much\n"
        ),
    ),
]
