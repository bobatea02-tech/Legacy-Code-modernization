      *****************************************************************
      * COMMON-DATA - Shared data structures across programs
      * This copybook is included in all programs
      *****************************************************************
       01  COMMON-CONSTANTS.
           05  CC-SYSTEM-NAME      PIC X(30) VALUE 
               "PAYMENT PROCESSING SYSTEM".
           05  CC-VERSION          PIC X(10) VALUE "V1.0.0".
           05  CC-MAX-RETRIES      PIC 9(2) VALUE 3.
       
       01  COMMON-WORK-AREAS.
           05  CW-CURRENT-DATE.
               10  CW-YEAR         PIC 9(4).
               10  CW-MONTH        PIC 9(2).
               10  CW-DAY          PIC 9(2).
           05  CW-CURRENT-TIME.
               10  CW-HOUR         PIC 9(2).
               10  CW-MINUTE       PIC 9(2).
               10  CW-SECOND       PIC 9(2).
           05  CW-ERROR-CODE       PIC X(4) VALUE SPACES.
           05  CW-ERROR-MESSAGE    PIC X(80) VALUE SPACES.
