# CareSmartz360 Hierarchical RAG Chatbot — Test Report

**Date/Time of Run:** 2026-06-01 13:32:06

**Test Endpoint:** `http://127.0.0.1:8000/api/hrag/chat`

## 📊 Executive Summary

| Metric | Value |
|---|---|
| **Total Test Cases Run** | 15 |
| **Passed** | 🟢 15 |
| **Warnings** | 🟡 0 |
| **Failed** | 🔴 0 |
| **Overall Functional Success Rate** | **100.0%** |
| **Average Latency** | **10.17 seconds** |
| **Total Combined Latency** | **152.56 seconds** |

## 📋 Comprehensive Test Matrix

| Test ID | Name | Category | Status | Latency | Referenced Sources | Chunks Matched | Remarks |
|---|---|---|---|---|---|---|---|
| `TC_001` | General/Basic Greeting | *Conversational* | **🟢 PASS** | 5.79s | 3 | 6 | Citations verified: 3 source(s) referenced. |
| `TC_002` | Procedural Shift Scheduling | *Procedural* | **🟢 PASS** | 4.03s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_003` | Add Caregiver | *Management* | **🟢 PASS** | 3.69s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_004` | Billing / Invoice Creation | *Billing* | **🟢 PASS** | 3.37s | 3 | 6 | Citations verified: 3 source(s) referenced. |
| `TC_005` | Client Profile Setup | *Management* | **🟢 PASS** | 3.56s | 3 | 6 | Citations verified: 3 source(s) referenced. |
| `TC_006` | Caregiver Clock In / Out | *Mobile App* | **🟢 PASS** | 12.96s | 3 | 6 | Citations verified: 3 source(s) referenced. |
| `TC_007` | Authorization Management | *Payer & Insurance* | **🟢 PASS** | 9.97s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_008` | EVV Configuration | *Compliance* | **🟢 PASS** | 5.52s | 3 | 3 | Citations verified: 3 source(s) referenced. |
| `TC_009` | Roles & Permissions | *Security* | **🟢 PASS** | 12.54s | 3 | 5 | Citations verified: 3 source(s) referenced. |
| `TC_010` | Custom Fields Setup | *Configuration* | **🟢 PASS** | 13.08s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_011` | Negative Test (Out of Domain) | *Negative Test* | **🟢 PASS** | 10.56s | 3 | 5 | Successfully declined out-of-domain query (matched fallback rules: ['not able to', 'does not contain']) |
| `TC_012` | Specific Scheduling Jargon (Split Shift) | *Procedural* | **🟢 PASS** | 7.62s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_013` | Partially Complete Query | *Short Query* | **🟢 PASS** | 18.26s | 3 | 3 | Citations verified: 3 source(s) referenced. |
| `TC_014` | Very Long Complex Scenario | *Complex Query* | **🟢 PASS** | 24.00s | 3 | 4 | Citations verified: 3 source(s) referenced. |
| `TC_015` | Special Characters Query | *Special Characters* | **🟢 PASS** | 17.65s | 3 | 6 | Citations verified: 3 source(s) referenced. |

## 🔍 Individual Test Logs

### 🧪 `TC_001` — General/Basic Greeting
- **Category:** Conversational
- **Status:** **🟢 PASS**
- **Latency:** 5.79 seconds
- **User Prompt:** *"Hello! Who are you and how can you help me?"*
- **Generated Response:**
  > I'm a helpful support assistant for CareSmartz360, a home care management software platform. I can help answer your questions about using the platform, troubleshoot issues, and provide guidance on how to get the most out of the system. If I don't have the answer to your question, I can suggest contacting CareSmartz360 support directly for further assistance. 
   
  Sources: 
  - How to Contact Caresmartz360 Support (https://www.intercom.help/caresmartz/en/articles/8264688-how-to-contact-caresmartz360-support) 
  - How to Contact Caresmartz360 Support (https://www.intercom.help/caresmartz/en/articles/1884028-how-to-contact-caresmartz360-support) 
  - How to Contact Caresmartz360 Support (https://www.intercom.help/caresmartz/en/articles/11632490-how-to-contact-caresmartz360-support)

- **Referenced Source Materials:**
  1. **How to Contact Caresmartz360 Support** — Score: `0.2758` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/8264688-how-to-contact-caresmartz360-support)
  2. **How to Contact Caresmartz360 Support** — Score: `0.2557` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1884028-how-to-contact-caresmartz360-support)
  3. **How to Contact Caresmartz360 Support** — Score: `0.2557` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/11632490-how-to-contact-caresmartz360-support)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "How to Contact Caresmartz360 Support"
  - `top_parent_score`: 0.2758

---

### 🧪 `TC_002` — Procedural Shift Scheduling
- **Category:** Procedural
- **Status:** **🟢 PASS**
- **Latency:** 4.03 seconds
- **User Prompt:** *"How do I schedule a shift in CareSmartz360?"*
- **Generated Response:**
  > To schedule a shift in CareSmartz360, follow these steps: 
  1. Mouse over the Scheduling icon in the main menu. 
  2. Click on the Schedule Calendar option from the drop-down menu. 
  3. Filter the calendar to show the desired client or caregiver. 
  4. Click on the "Add New Shift" option to create a new shift. 
  5. Fill in the required details for the shift, such as date, time, client, and caregiver. 
  6. Save the new shift. 
   
  You can also use other options under the Scheduling section to manage and create shifts, such as quickly creating new shifts or matching clients with qualified caregivers. 
   
  Sources: 
  - Take a Tour of CareSmartz360  
  - Office Settings> Main Tab Article  
  - Complete Tasks on Schedules

- **Referenced Source Materials:**
  1. **Take a Tour of CareSmartz360** — Score: `0.7756` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/4891341-take-a-tour-of-caresmartz360)
  2. **Office Settings> Main Tab Article** — Score: `0.7146` | Matched Chunks: `1`
  3. **Complete Tasks on Schedules** — Score: `0.7138` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/6078890-complete-tasks-on-schedules)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Take a Tour of CareSmartz360"
  - `top_parent_score`: 0.7756

---

### 🧪 `TC_003` — Add Caregiver
- **Category:** Management
- **Status:** **🟢 PASS**
- **Latency:** 3.69 seconds
- **User Prompt:** *"How do I add a new caregiver into the system?"*
- **Generated Response:**
  > To add a new caregiver into the system, follow these steps: 
  1. Log into the system as an Agency User, Owner, or Admin. 
  2. Navigate to the Caregivers module and click on the caregiver link. 
  3. Click the green "Add" button to add a new caregiver. 
  4. Fill out the required fields marked with a red asterisk, including the office field (if you have multiple offices), username, hire date, territory selection (if applicable), and email address. 
  5. Enter additional information as needed, such as social security number, phone number, and physical address. 
  6. Click the "Save" button to save the caregiver's profile. 
   
  Note: It's recommended to choose a consistent format for usernames, such as first initial and last name (e.g., JDoe). Also, make sure to enter a phone number and mark it as primary, but avoid marking it as time tracking. 
   
  Sources: 
  - How to Add a Caregiver 
  - Add A Caregiver 
  - Add a Caregiver

- **Referenced Source Materials:**
  1. **How to Add a Caregiver** — Score: `0.7167` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1883977-how-to-add-a-caregiver)
  2. **Add A Caregiver** — Score: `0.6966` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/10670830-add-a-caregiver)
  3. **Add a Caregiver** — Score: `0.6966` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/10670863-add-a-caregiver)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "How to Add a Caregiver"
  - `top_parent_score`: 0.7167

---

### 🧪 `TC_004` — Billing / Invoice Creation
- **Category:** Billing
- **Status:** **🟢 PASS**
- **Latency:** 3.37 seconds
- **User Prompt:** *"What is the process to create an invoice for a client?"*
- **Generated Response:**
  > To create an invoice for a client, follow these steps: 
  1. Log into the system as an Agency User, Owner, or Admin. 
  2. Click Create Invoice(s) under the Accounting menu. 
  3. Enter the search/filter parameters and click the Apply button to search for approved schedules that are not billed/finalized yet. 
  4. Review, edit, or add visits as necessary. 
  5. If needed, click the Recalculate button to update the visit totals after making edits. 
  6. Choose the clients/visits to create invoices for. 
  7. Click the Create Invoice Button and choose an Invoice Date. 
  8. Click Save to finalize the selected invoices. 
   
  For ALP clients, additional steps are required: 
  1. Select the ALP client under the Clients menu. 
  2. Ensure the client is marked as an ALP client and edit their profile if needed. 
  3. Add a payer and set the start date. 
  4. Update the schedule status to Approved and enter custom bill and pay rates. 
  5. Follow the prompts to create and finalize the invoice. 
   
  Sources: 
  - Create an Invoice (Billing) 
  - Create an ALP Invoice

- **Referenced Source Materials:**
  1. **Create an Invoice (Billing)** — Score: `0.6533` | Matched Chunks: `3`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/8651133-create-an-invoice-billing)
  2. **Client Portal Login** — Score: `0.6193` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1884100-client-portal-login)
  3. **Create an ALP Invoice** — Score: `0.5805` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1884043-create-an-alp-invoice)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Create an Invoice (Billing)"
  - `top_parent_score`: 0.6533

---

### 🧪 `TC_005` — Client Profile Setup
- **Category:** Management
- **Status:** **🟢 PASS**
- **Latency:** 3.56 seconds
- **User Prompt:** *"How do I add a client and set up their profile?"*
- **Generated Response:**
  > To add a client and set up their profile, follow these steps: 
  1. Log into the system as an Agency User, Owner, or Admin. 
  2. Click the Clients module. 
  3. Click the + green button on the right to add a new client. 
  4. Select "Add New Client" to create a new client profile. 
  5. Fill in the required information, including fields marked with red asterisks. 
  6. Add address information, phone number details, and referral sources. 
  7. Configure billing preferences and schedule preferences as needed. 
  8. Click the Save button at the bottom right corner of the screen to save the client's profile. 
   
  If the client is a prospective client, you can also select "Prospective Client" and follow the prompts to set up their profile. 
   
  Sources: 
  - Prospective Client Configuration 
  - Clients & Payers Overview

- **Referenced Source Materials:**
  1. **Prospective Client Configuration** — Score: `0.5749` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5586336-prospective-client-configuration)
  2. **Configure Client profile with Payer(s)** — Score: `0.5567` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1883934-configure-client-profile-with-payer-s)
  3. **Clients & Payers Overview** — Score: `0.5493` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/13143774-clients-payers-overview)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Prospective Client Configuration"
  - `top_parent_score`: 0.5749

---

### 🧪 `TC_006` — Caregiver Clock In / Out
- **Category:** Mobile App
- **Status:** **🟢 PASS**
- **Latency:** 12.96 seconds
- **User Prompt:** *"How do caregivers clock in and out using the mobile app?"*
- **Generated Response:**
  > To clock in and out using the mobile app, caregivers must be within the threshold time and distance defined in the Office Settings. Here's how to troubleshoot if they're having issues: 
  1. Ensure location services are activated on the caregiver's device. 
  2. Verify the caregiver is within the minimum radius set in the Office Settings. 
  3. Check if the client has the "Allow Clock-in/Clock-out from Caregiver Mobile" box checked. 
  4. Confirm the caregiver is using the correct Agency ID and Time-Tracking Number. 
  5. If issues persist, check the message received by the caregiver and work with them or your admin to make adjustments. 
   
  Sources: 
  - Caregivers unable to clock-in/clock-out 
  - Office Settings> Main Tab Article 
  - Caregiver message “User is not within the range defined by the agency”

- **Referenced Source Materials:**
  1. **Caregivers unable to clock-in/clock-out** — Score: `0.8114` | Matched Chunks: `4`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/2132438-caregivers-unable-to-clock-in-clock-out)
  2. **Office Settings> Main Tab Article** — Score: `0.7921` | Matched Chunks: `1`
  3. **Caregiver message “User is not within the range defined by the agency”.** — Score: `0.7818` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/2132618-caregiver-message-user-is-not-within-the-range-defined-by-the-agency)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Caregivers unable to clock-in/clock-out"
  - `top_parent_score`: 0.8114

---

### 🧪 `TC_007` — Authorization Management
- **Category:** Payer & Insurance
- **Status:** **🟢 PASS**
- **Latency:** 9.97 seconds
- **User Prompt:** *"How to set up billing authorization in CareSmartz360?"*
- **Generated Response:**
  > To set up billing authorization in CareSmartz360, follow these steps: 
  1. Create separate service types for each service you provide with different rates (e.g., Personal Care--Private Pay, Personal Care--Medicaid) in Admin Settings > Scheduling > Service Type. 
  2. Configure each service type by editing the fields, such as default bill units and type. 
  3. Set default rates for each service type in Office Settings > Rates, including the pay rate for caregivers. 
  4. Add payers (companies or individuals) in Clients > Payers and complete the required fields. 
  5. Associate payers with clients by going to Clients > Clients > Open a client profile > Rates Tab and selecting Add Existing Payer. 
  6. Indicate the order of payment (primary or secondary) and add the Member ID from the insurance. 
  7. Select Client Authorization as the Payment Distribution and add authorization details. 
  8. Save the authorization and payer to the client profile. 
   
  Sources: 
  - Authorizations from Start to Finish  
  - CareSmartz360 Open API  
  - Paychex Integration

- **Referenced Source Materials:**
  1. **CareSmartz360 Open API** — Score: `0.7622` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/12326740-caresmartz360-open-api)
  2. **Authorizations from Start to Finish** — Score: `0.7552` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/3269879-authorizations-from-start-to-finish)
  3. **Paychex Integration** — Score: `0.7315` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5111457-paychex-integration)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "CareSmartz360 Open API"
  - `top_parent_score`: 0.7622

---

### 🧪 `TC_008` — EVV Configuration
- **Category:** Compliance
- **Status:** **🟢 PASS**
- **Latency:** 5.52 seconds
- **User Prompt:** *"What is EVV and how is it configured in CareSmartz360?"*
- **Generated Response:**
  > Electronic Visit Verification (EVV) is a system used to verify the occurrence of home care visits. To configure EVV in CareSmartz360, follow these steps for CareBridge integration: 
  1. Register your agency with CareBridge. 
  2. Confirm technical setup with your Onboarding Specialist or CareSmartz360 contact. 
  3. Complete your admin EVV settings in Admin Settings > EVV Configuration. 
  4. Set up CareBridge as the aggregator in Payer Profiles for each relevant payer. 
  5. Enter reason codes when manually adjusting schedules. 
  6. Submit visits to CareBridge using the CareBridge Manual Data Post report. 
  7. Check for errors and fix them. 
  8. Export visits to claims in the CareBridge portal. 
   
  For HHA Exchange integration, register CareSmartz360 as your 3rd Party EVV Vendor with HHA by submitting a request via their Client Support Portal. 
   
  Sources: 
  - HHA Registration 
  - Posting your EVV Data to HHA Exchange Webinar 
  - General Carebridge Help Guide

- **Referenced Source Materials:**
  1. **HHA Registration** — Score: `0.6300` | Matched Chunks: `1`
  2. **Posting your EVV Data to HHA Exchange Webinar** — Score: `0.6137` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5162033-posting-your-evv-data-to-hha-exchange-webinar)
  3. **General Carebridge Help Guide** — Score: `0.5929` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/11635316-general-carebridge-help-guide)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "HHA Registration"
  - `top_parent_score`: 0.6300

---

### 🧪 `TC_009` — Roles & Permissions
- **Category:** Security
- **Status:** **🟢 PASS**
- **Latency:** 12.54 seconds
- **User Prompt:** *"How can I edit office staff roles and scheduling permissions?"*
- **Generated Response:**
  > To edit office staff roles, you can create custom roles in the system, which allows you to customize permissions so that users can review the system per the permissions set by the Admin.  
   
  For scheduling permissions, you can edit the client's schedule and access the client's details through the Agency User Admin App. You can also edit the caregiver's details and schedules.  
   
  However, to fully customize roles and permissions, you may need to refer to the article "Create and Manage Custom Roles" which is mentioned in the "Add Office Staff" article. 
   
  Sources: 
  - Add Office Staff  
  - Agency User Admin App  
  - Office Staff Payroll

- **Referenced Source Materials:**
  1. **Add Office Staff** — Score: `0.6049` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/15018805-add-office-staff)
  2. **Agency User Admin App** — Score: `0.5863` | Matched Chunks: `3`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5599465-agency-user-admin-app)
  3. **Office Staff Payroll** — Score: `0.5538` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5452835-office-staff-payroll)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Add Office Staff"
  - `top_parent_score`: 0.6049

---

### 🧪 `TC_010` — Custom Fields Setup
- **Category:** Configuration
- **Status:** **🟢 PASS**
- **Latency:** 13.08 seconds
- **User Prompt:** *"How do I create a custom field for client details?"*
- **Generated Response:**
  > To create a custom field for client details, you can configure the fields in the Prospective Client Form settings.  
   
  1. Navigate to Settings. 
  2. Open All Settings. 
  3. Select Clients. 
  4. Click Prospective Client Form Settings. 
   
  In the Prospective Client Form settings, you can control which fields appear on the form and set each field as mandatory, optional, or disabled.  
   
  However, the provided context does not fully explain how to create a completely custom field. For more information on creating custom fields, I suggest contacting CareSmartz360 support. 
   
  Sources: 
  --- Source 1: Client Module - Add Prospective Client --- 
  --- Source 3: Client Module - Clients - Prospective Client Form ---

- **Referenced Source Materials:**
  1. **Client Module - Add Prospective Client** — Score: `0.5655` | Matched Chunks: `2`
  2. **Add Clients** — Score: `0.5478` | Matched Chunks: `1`
  3. **Client Module - Clients - Prospective Client Form** — Score: `0.5278` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/13976858-client-module-clients-prospective-client-form)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Client Module - Add Prospective Client"
  - `top_parent_score`: 0.5655

---

### 🧪 `TC_011` — Negative Test (Out of Domain)
- **Category:** Negative Test
- **Status:** **🟢 PASS**
- **Latency:** 10.56 seconds
- **User Prompt:** *"What is the recipe for baking a chocolate chip cookie?"*
- **Generated Response:**
  > I'm not able to provide a recipe for baking a chocolate chip cookie as the provided article context does not contain this information. The articles are related to the CareSmartz360 home care management software platform and do not include recipes or cooking instructions. If you have any questions about CareSmartz360, I'd be happy to help. 
   
  Sources: 
  None of the provided articles are relevant to this question.

- **Referenced Source Materials:**
  1. **Clear a Browser's Cache (Safari - Mac)** — Score: `0.1783` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/5363026-clear-a-browser-s-cache-safari-mac)
  2. **Payroll - Gusto** — Score: `0.1710` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/12961040-payroll-gusto)
  3. **What's New - October 31, 2023** — Score: `0.1684` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/8504997-what-s-new-october-31-2023)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Clear a Browser's Cache (Safari - Mac)"
  - `top_parent_score`: 0.1783

---

### 🧪 `TC_012` — Specific Scheduling Jargon (Split Shift)
- **Category:** Procedural
- **Status:** **🟢 PASS**
- **Latency:** 7.62 seconds
- **User Prompt:** *"How do I set up a split shift in CareSmartz360?"*
- **Generated Response:**
  > To set up a split shift in CareSmartz360, follow these steps: 
  1. Go to Office settings -> Payroll section. 
  2. Enable the checkbox for allowing the splitting of schedules at midnight. 
  3. CareSmartz360 will prompt you to enable it for all clients. If you choose yes, it will be enabled for all clients under client -> main tab. 
  4. If you want to turn off the splitting for a specific client, go to the client's profile in the main tab and disable it by unchecking the "split overnight shift applicable" and click on update. 
   
  Sources: 
  - Overnight Split Shift 
  - What's New - August 12, 2020

- **Referenced Source Materials:**
  1. **Overnight Split Shift** — Score: `0.6445` | Matched Chunks: `1`
  2. **Open Shifts Widget** — Score: `0.5680` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/4967405-open-shifts-widget)
  3. **What's New - August 12, 2020** — Score: `0.5525` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/4321568-what-s-new-august-12-2020)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Overnight Split Shift"
  - `top_parent_score`: 0.6445

---

### 🧪 `TC_013` — Partially Complete Query
- **Category:** Short Query
- **Status:** **🟢 PASS**
- **Latency:** 18.26 seconds
- **User Prompt:** *"caregiver scheduling conflicts"*
- **Generated Response:**
  > To manage caregiver scheduling conflicts, you can use the Alerts tab in the office settings. This feature allows you to set alerts for possible scheduling problems, such as: 
  1. Schedule Overlaps: when a caregiver is assigned to be in two places at the same time. 
  2. Caregiver Compliance: when a caregiver has an expired license or certification. 
  3. Caregiver Not Preferred: when a caregiver is not preferred for a specific client. 
  4. Caregiver Not Available: when a caregiver has entered unavailability for a specific time. 
  5. Exceeds Weekly or Daily Hours: when assigning a shift would cause the caregiver to exceed the allowed hours, resulting in overtime pay. 
   
  You can choose to receive alerts or prohibit the creation of a schedule that conflicts with these settings. Additionally, you can also use the Caregiver Availability feature to add or edit caregiver availability and unavailability, which can help prevent scheduling conflicts. 
   
  Sources: 
  - Office Settings> Alerts Article 
  - Caregiver Availability Overview  
  - Scheduling

- **Referenced Source Materials:**
  1. **Office Settings> Alerts Article** — Score: `0.7138` | Matched Chunks: `1`
  2. **Caregiver Availability Overview** — Score: `0.7091` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/1884025-caregiver-availability-overview)
  3. **Scheduling** — Score: `0.7020` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/12956074-scheduling)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Office Settings> Alerts Article"
  - `top_parent_score`: 0.7138

---

### 🧪 `TC_014` — Very Long Complex Scenario
- **Category:** Complex Query
- **Status:** **🟢 PASS**
- **Latency:** 24.00 seconds
- **User Prompt:** *"I am trying to run payroll for the caregiver John Doe but the shift hours are not showing up correctly in the billing section, how do I resolve this payroll issue?"*
- **Generated Response:**
  > To resolve the payroll issue, you can try the following steps: 
   
  1. Check the Office Settings > Billing section to ensure that the "Do you charge OT on client invoices?" setting is configured correctly. 
  2. Verify that the caregiver's profile and the client's profile are set up correctly, including the pay rates and billing information. 
  3. Review the shift details to ensure that the hours are being tracked correctly and that there are no errors in the time tracking data. 
  4. Check the Payroll Tab in the Office Settings to ensure that the payroll period and frequency are set up correctly. 
  5. If you are using a payroll processor like ADP or Paychex, ensure that the integration is set up correctly and that the data is being synced correctly. 
   
  If none of these steps resolve the issue, it's recommended to contact CareSmartz360 support for further assistance. 
   
  Sources: 
  - What's New - September 30, 2020 
  - Office Settings - Payroll Tab

- **Referenced Source Materials:**
  1. **What's New - September 30, 2020** — Score: `0.6269` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/4466230-what-s-new-september-30-2020)
  2. **New Features and Updates - Jan'19** — Score: `0.6207` | Matched Chunks: `2`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/2582697-new-features-and-updates-jan-19)
  3. **Office Settings - Payroll Tab** — Score: `0.6148` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/13163108-office-settings-payroll-tab)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "What's New - September 30, 2020"
  - `top_parent_score`: 0.6269

---

### 🧪 `TC_015` — Special Characters Query
- **Category:** Special Characters
- **Status:** **🟢 PASS**
- **Latency:** 17.65 seconds
- **User Prompt:** *"How do I update settings & billing info for client's family portal?"*
- **Generated Response:**
  > To update settings and billing info for a client's family portal, you need to access the client's profile and then navigate to the Billing Info & Settings section.  
   
  Here are the steps: 
  1. Enter the particular Client’s Profile. 
  2. Click on Billing Info & Settings. 
  3. The page displays the list of Payers for the client you are viewing. 
  4. To add a new payer or update an existing one, click the green + symbol on the top right of the screen or edit the existing payer. 
  5. Update the required information such as address, phone number, email, and invoice settings. 
   
  If you need to update the "bill to" address, you will need to access the Payer profile, as the "bill to" address is associated with the Payer, not the client. 
   
  Sources: 
  - Clients & Payers Overview 
  - Client Module - Clients - Client Listing 
  - Change the "bill to" address

- **Referenced Source Materials:**
  1. **Clients & Payers Overview** — Score: `0.5589` | Matched Chunks: `4`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/13143774-clients-payers-overview)
  2. **Client Module - Clients - Client Listing** — Score: `0.5434` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/13975186-client-module-clients-client-listing)
  3. **Change the "bill to" address** — Score: `0.5398` | Matched Chunks: `1`
     [Open Source Link](https://www.intercom.help/caresmartz/en/articles/3062033-change-the-bill-to-address)
- **Vector Index Debug Logs:**
  - `parents_retrieved`: 3
  - `top_parent_title`: "Clients & Payers Overview"
  - `top_parent_score`: 0.5589

---
