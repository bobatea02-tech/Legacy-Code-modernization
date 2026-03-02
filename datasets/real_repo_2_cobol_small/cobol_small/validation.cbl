       IDENTIFICATION DIVISION.
       PROGRAM-ID. VALIDATION.
       AUTHOR. LEGACY-SYSTEM.
      *****************************************************************
      * Validation program - Validates customer and payment data
      * Called by main program
      *****************************************************************
       
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-370.
       OBJECT-COMPUTER. IBM-370.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY COMMON-DATA.
       
       01  WS-MIN-PAYMENT          PIC 9(7)V99 VALUE 10.00.
       01  WS-MAX-PAYMENT          PIC 9(7)V99 VALUE 99999.99.
       01  WS-MIN-CUSTOMER-ID      PIC 9(8) VALUE 10000000.
       01  WS-MAX-CUSTOMER-ID      PIC 9(8) VALUE 99999999.
       
       LINKAGE SECTION.
       01  LS-CUSTOMER-ID          PIC 9(8).
       01  LS-PAYMENT-AMOUNT       PIC 9(7)V99.
       01  LS-VALIDATION-STATUS    PIC X.
       
       PROCEDURE DIVISION USING LS-CUSTOMER-ID
                                LS-PAYMENT-AMOUNT
                                LS-VALIDATION-STATUS.
       VALIDATION-LOGIC.
           DISPLAY "VALIDATION: CHECKING CUSTOMER ID".
           
      *    Legacy anti-pattern: Nested IF statements (should use EVALUATE)
           IF LS-CUSTOMER-ID < WS-MIN-CUSTOMER-ID
               MOVE 'N' TO LS-VALIDATION-STATUS
               DISPLAY "VALIDATION: CUSTOMER ID TOO LOW"
           ELSE
               IF LS-CUSTOMER-ID > WS-MAX-CUSTOMER-ID
                   MOVE 'N' TO LS-VALIDATION-STATUS
                   DISPLAY "VALIDATION: CUSTOMER ID TOO HIGH"
               ELSE
                   IF LS-PAYMENT-AMOUNT < WS-MIN-PAYMENT
                       MOVE 'N' TO LS-VALIDATION-STATUS
                       DISPLAY "VALIDATION: PAYMENT AMOUNT TOO LOW"
                   ELSE
                       IF LS-PAYMENT-AMOUNT > WS-MAX-PAYMENT
                           MOVE 'N' TO LS-VALIDATION-STATUS
                           DISPLAY "VALIDATION: PAYMENT AMOUNT TOO HIGH"
                       ELSE
                           MOVE 'Y' TO LS-VALIDATION-STATUS
                           DISPLAY "VALIDATION: ALL CHECKS PASSED"
                       END-IF
                   END-IF
               END-IF
           END-IF.
           
           GOBACK.
