# Attendance Punch System

## Overview

The attendance punch system has been simplified to handle only two actions: **Check In** and **Check Out**. This system is designed to work with a frontend that provides a single button that toggles between check-in and check-out states.

## Key Features

1. **Simplified Actions**: Only two actions supported - `check_in` and `check_out`
2. **Working Hours Calculation**: Automatically calculates working hours when employee checks out
3. **Status Tracking**: Tracks employee attendance status throughout the day
4. **Validation**: Prevents duplicate check-ins and ensures proper check-out sequence

## API Endpoints

### 1. Attendance Punch (POST)
**Endpoint**: `/api/attendance/punch/`

**Request Body**:
```json
{
    "employee": 1,
    "action_type": "check_in",  // or "check_out"
    "source_id": 1,             // optional
    "remarks": "Optional remarks" // optional
}
```

**Response for Check-in**:
```json
{
    "data": {
        "message": "Check-in successful",
        "employee": 1,
        "check_in_time": "2024-01-15T09:00:00Z",
        "attendance_id": 123,
        "status": "checked_in"
    },
    "status": "200"
}
```

**Response for Check-out**:
```json
{
    "data": {
        "message": "Check-out successful",
        "employee": 1,
        "check_in_time": "2024-01-15T09:00:00Z",
        "check_out_time": "2024-01-15T17:00:00Z",
        "working_hours": 8.0,
        "attendance_id": 123,
        "status": "checked_out"
    },
    "status": "200"
}
```

### 2. Get Employee Status (GET)
**Endpoint**: `/api/attendance/punch/?employee=1`

**Response**:
```json
{
    "data": {
        "employee": 1,
        "status": "checked_in",  // or "checked_out" or "not_checked_in"
        "check_in_time": "2024-01-15T09:00:00Z",
        "check_out_time": "2024-01-15T17:00:00Z",  // only if checked out
        "working_hours": 8.0,  // only if checked out
        "message": "Employee is currently checked in"
    },
    "status": "200"
}
```

## Frontend Integration

### Button State Management

The frontend should implement a single button that changes based on the employee's current status:

1. **Initial State**: Button shows "Check In"
2. **After Check-in**: Button changes to "Check Out"
3. **After Check-out**: Button shows "Check In" (for next day)

### Example Frontend Logic

```javascript
// Get employee status
async function getEmployeeStatus(employeeId) {
    const response = await fetch(`/api/attendance/punch/?employee=${employeeId}`);
    const data = await response.json();
    return data.data;
}

// Handle button click
async function handleAttendancePunch(employeeId) {
    const status = await getEmployeeStatus(employeeId);
    
    let actionType;
    if (status.status === 'not_checked_in' || status.status === 'checked_out') {
        actionType = 'check_in';
    } else if (status.status === 'checked_in') {
        actionType = 'check_out';
    }
    
    const response = await fetch('/api/attendance/punch/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            employee: employeeId,
            action_type: actionType
        })
    });
    
    const result = await response.json();
    return result;
}

// Update button text
function updateButtonText(status) {
    const button = document.getElementById('attendance-button');
    if (status.status === 'checked_in') {
        button.textContent = 'Check Out';
        button.className = 'btn btn-warning';
    } else {
        button.textContent = 'Check In';
        button.className = 'btn btn-success';
    }
}
```

## Database Models

### Attendance Model
```python
class Attendance(models.Model):
    employee = models.IntegerField()
    attendance_type = models.ForeignKey('AttendanceType')
    action = models.ForeignKey('Action')  # check_in or check_out
    date_check_in = models.DateTimeField()
    date_check_out = models.DateTimeField(null=True, blank=True)
    working_hour = models.FloatField(null=True, blank=True)
    # ... other fields
```

### Action Model
```python
class Action(models.Model):
    name = models.CharField(max_length=50)  # "Check In", "Check Out"
    code = models.CharField(max_length=20)  # "check_in", "check_out"
    # ... other fields
```

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Setup Required Data
```bash
python manage.py setup_actions
```

### 3. Test the Functionality
```bash
python test_attendance_punch.py
```

## Service Methods

### AttendanceService.process_attendance_punch()
Main method for processing check-in and check-out actions.

**Parameters**:
- `employee_id`: Employee ID
- `action_type`: "check_in" or "check_out"
- `source_id`: Optional source ID
- `remarks`: Optional remarks

**Returns**: Dictionary with result or error message

### AttendanceService.get_employee_attendance_status()
Get current employee attendance status.

**Parameters**:
- `employee_id`: Employee ID

**Returns**: Dictionary with employee status information

## Utility Functions

### calculate_working_hours(attendance)
Calculate working hours from attendance record.

### validate_attendance_punch(employee_id, action_type)
Validate attendance punch request before processing.

### get_employee_attendance_status(employee_id)
Get employee's current attendance status for today.

## Error Handling

The system handles various error scenarios:

1. **Duplicate Check-in**: Employee already checked in today
2. **No Check-in Found**: Trying to check out without checking in first
3. **Invalid Action Type**: Only "check_in" and "check_out" are supported
4. **Missing Data**: Required attendance types or actions not found

## Working Hours Calculation

Working hours are automatically calculated when an employee checks out:

```python
if attendance.date_check_in and attendance.date_check_out:
    time_diff = attendance.date_check_out - attendance.date_check_in
    working_hours = time_diff.total_seconds() / 3600  # Convert to hours
    attendance.working_hour = round(working_hours, 2)
```

## Security Considerations

1. **Input Validation**: All inputs are validated through serializers
2. **Transaction Safety**: All operations use database transactions
3. **Error Handling**: Comprehensive error handling and logging
4. **Data Integrity**: Prevents duplicate records and invalid states

## Testing

The system includes comprehensive testing:

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: End-to-end API testing
3. **Test Script**: `test_attendance_punch.py` for manual testing

## Future Enhancements

1. **Shift Integration**: Automatic shift assignment based on time
2. **Late Calculation**: Calculate late minutes based on shift start time
3. **Overtime Calculation**: Calculate overtime hours
4. **Location Tracking**: Add location-based attendance
5. **Mobile Support**: Mobile app integration 