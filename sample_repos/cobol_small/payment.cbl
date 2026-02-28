       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYMENT.
       AUTHOR. LEGACY-SYSTEM.
      *****************************************************************
      * Payment processing program - Processes validated payments
      * Called by main program after validation
      *****************************************************************
       
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-370.
       OBJECT-COMPUTER. IBM-370.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY COMMON-DATA.
       
       01  WS-TRANSACTION-ID       PIC 9(10) VALUE ZEROS.
       01  WS-PROCESSING-FEE       PIC 9(5)V99 VALUE ZEROS.
       01  WS-TOTAL-AMOUNT         PIC 9(7)V99 VALUE ZEROS.
       01  WS-FEE-RATE             PIC 9V9999 VALUE 0.0250.
       
       LINKAGE SECTION.
       01  LS-CUSTOMER-ID          PIC 9(8).
       01  LS-PAYMENT-AMOUNT       PIC 9(7)V99.
       01  LS-PROCESS-STATUS       PIC X.
       
       PROCEDURE DIVISION USING LS-CUSTOMER-ID
                                LS-PAYMENT-AMOUNT
                                LS-PROCESS-STATUS.
       PAYMENT-LOGIC.
           DISPLAY "PAYMENT: PROCESSING TRANSACTION".
           
      *    Generate transaction ID
           COMPUTE WS-TRANSACTION-ID = 
               FUNCTION RANDOM * 9999999999.
           
      *    Calculate processing fee
           COMPUTE WS-PROCESSING-FEE = 
               LS-PAYMENT-AMOUNT * WS-FEE-RATE.
           
      *    Calculate total amount
           COMPUTE WS-TOTAL-AMOUNT = 
               LS-PAYMENT-AMOUNT + WS-PROCESSING-FEE.
           
           DISPLAY "PAYMENT: TRANSACTION ID: " WS-TRANSACTION-ID.
           DISPLAY "PAYMENT: BASE AMOUNT: " LS-PAYMENT-AMOUNT.
           DISPLAY "PAYMENT: PROCESSING FEE: " WS-PROCESSING-FEE.
           DISPLAY "PAYMENT: TOTAL AMOUNT: " WS-TOTAL-AMOUNT.
           
      *    Simulate payment processing
           IF WS-TOTAL-AMOUNT > 0
               MOVE 'S' TO LS-PROCESS-STATUS
               DISPLAY "PAYMENT: TRANSACTION COMPLETED"
           ELSE
               MOVE 'F' TO LS-PROCESS-STATUS
               DISPLAY "PAYMENT: TRANSACTION FAILED"
           END-IF.
           
           GOBACK.
