       IDENTIFICATION DIVISION.
       PROGRAM-ID. UNUSED-MODULE.
       AUTHOR. LEGACY-SYSTEM.
      *****************************************************************
      * Unused module - Not called by any program
      * Included for validation testing purposes
      *****************************************************************
       
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER. IBM-370.
       OBJECT-COMPUTER. IBM-370.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-DUMMY-FIELD          PIC X(50) VALUE SPACES.
       
       PROCEDURE DIVISION.
       UNUSED-LOGIC.
           DISPLAY "THIS MODULE IS NEVER CALLED".
           STOP RUN.
