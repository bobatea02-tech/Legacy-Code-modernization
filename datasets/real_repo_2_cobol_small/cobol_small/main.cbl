       IDENTIFICATION DIVISION.
       PROGRAM-ID. MAIN-PROGRAM.
       AUTHOR. LEGACY-SYSTEM.
      *****************************************************************
      * Main program - Entry point for payment processing system
      * Demonstrates cross-program calls and data sharing
      *****************************************************************
       
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-370.
       OBJECT-COMPUTER. IBM-370.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY COMMON-DATA.
       
       01  WS-PAYMENT-AMOUNT       PIC 9(7)V99 VALUE ZEROS.
       01  WS-CUSTOMER-ID          PIC 9(8) VALUE ZEROS.
       01  WS-VALIDATION-STATUS    PIC X VALUE SPACE.
           88 VALID-PAYMENT        VALUE 'Y'.
           88 INVALID-PAYMENT      VALUE 'N'.
       01  WS-PROCESS-STATUS       PIC X VALUE SPACE.
           88 PROCESS-SUCCESS      VALUE 'S'.
           88 PROCESS-FAILURE      VALUE 'F'.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "=================================".
           DISPLAY "PAYMENT PROCESSING SYSTEM STARTED".
           DISPLAY "=================================".
           
           MOVE 12345678 TO WS-CUSTOMER-ID.
           MOVE 1500.75 TO WS-PAYMENT-AMOUNT.
           
           DISPLAY "CUSTOMER ID: " WS-CUSTOMER-ID.
           DISPLAY "PAYMENT AMOUNT: " WS-PAYMENT-AMOUNT.
           
      *    Call validation program
           CALL 'VALIDATION' USING WS-CUSTOMER-ID
                                   WS-PAYMENT-AMOUNT
                                   WS-VALIDATION-STATUS.
           
           IF VALID-PAYMENT
               DISPLAY "VALIDATION PASSED"
               PERFORM PROCESS-PAYMENT
           ELSE
               DISPLAY "VALIDATION FAILED"
               MOVE 'F' TO WS-PROCESS-STATUS
           END-IF.
           
           IF PROCESS-SUCCESS
               DISPLAY "PAYMENT PROCESSED SUCCESSFULLY"
           ELSE
               DISPLAY "PAYMENT PROCESSING FAILED"
           END-IF.
           
           DISPLAY "=================================".
           DISPLAY "SYSTEM TERMINATED".
           STOP RUN.
       
       PROCESS-PAYMENT.
      *    Call payment processing program
           CALL 'PAYMENT' USING WS-CUSTOMER-ID
                                WS-PAYMENT-AMOUNT
                                WS-PROCESS-STATUS.
