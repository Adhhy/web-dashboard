
# Timetable Creation (Hardcoded)

## Table Definition

CREATE TABLE timetable (
    day TEXT,
    period INTEGER,
    subject_code TEXT,
    PRIMARY KEY (day, period)
);

## Timetable Data

### MONDAY
INSERT INTO timetable VALUES ('MONDAY', 1, 'AAD');
INSERT INTO timetable VALUES ('MONDAY', 2, 'IEFT');
INSERT INTO timetable VALUES ('MONDAY', 3, 'PE');
INSERT INTO timetable VALUES ('MONDAY', 4, 'CGIP');
INSERT INTO timetable VALUES ('MONDAY', 5, 'CD');
INSERT INTO timetable VALUES ('MONDAY', 6, 'AAD');
INSERT INTO timetable VALUES ('MONDAY', 7, 'CD');

### TUESDAY
INSERT INTO timetable VALUES ('TUESDAY', 1, 'CD');
INSERT INTO timetable VALUES ('TUESDAY', 2, 'CGIP');
INSERT INTO timetable VALUES ('TUESDAY', 3, 'PE');
INSERT INTO timetable VALUES ('TUESDAY', 4, 'CD');
INSERT INTO timetable VALUES ('TUESDAY', 5, NULL); -- Net/Mini Lab
INSERT INTO timetable VALUES ('TUESDAY', 6, NULL); -- Net/Mini Lab
INSERT INTO timetable VALUES ('TUESDAY', 7, NULL); -- Net/Mini Lab

### WEDNESDAY
INSERT INTO timetable VALUES ('WEDNESDAY', 1, 'PE');
INSERT INTO timetable VALUES ('WEDNESDAY', 2, 'AAD');
INSERT INTO timetable VALUES ('WEDNESDAY', 3, 'IEFT');
INSERT INTO timetable VALUES ('WEDNESDAY', 4, NULL); -- Advisory/Comp
INSERT INTO timetable VALUES ('WEDNESDAY', 5, NULL); -- Net/Mini Lab
INSERT INTO timetable VALUES ('WEDNESDAY', 6, NULL); -- Net/Mini Lab
INSERT INTO timetable VALUES ('WEDNESDAY', 7, NULL); -- Net/Mini Lab

### THURSDAY
INSERT INTO timetable VALUES ('THURSDAY', 1, 'AAD');
INSERT INTO timetable VALUES ('THURSDAY', 2, 'IEFT');
INSERT INTO timetable VALUES ('THURSDAY', 3, 'PE');
INSERT INTO timetable VALUES ('THURSDAY', 4, 'CD');
INSERT INTO timetable VALUES ('THURSDAY', 5, 'CCW');
INSERT INTO timetable VALUES ('THURSDAY', 6, 'AAD');
INSERT INTO timetable VALUES ('THURSDAY', 7, 'CGIP');

### FRIDAY
INSERT INTO timetable VALUES ('FRIDAY', 1, 'CGIP');
INSERT INTO timetable VALUES ('FRIDAY', 2, NULL); -- Placement
INSERT INTO timetable VALUES ('FRIDAY', 3, NULL); -- Placement
INSERT INTO timetable VALUES ('FRIDAY', 4, NULL); -- Placement
INSERT INTO timetable VALUES ('FRIDAY', 5, NULL); -- Placement
INSERT INTO timetable VALUES ('FRIDAY', 6, 'CGIP');
INSERT INTO timetable VALUES ('FRIDAY', 7, 'PE');
