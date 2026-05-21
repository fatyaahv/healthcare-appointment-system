<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:h="https://www.saglikrandevu.com/schema">

    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:template match="/">
        <html>
            <head>
                <meta charset="UTF-8"/>
                <title>Healthcare Appointment Report</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 32px;
                        color: #222;
                        background: #f6f8fb;
                    }

                    h1, h2 {
                        color: #17415f;
                    }

                    .summary {
                        display: grid;
                        grid-template-columns: repeat(4, minmax(120px, 1fr));
                        gap: 12px;
                        margin-bottom: 28px;
                    }

                    .metric {
                        background: #ffffff;
                        border: 1px solid #d9e1ea;
                        border-radius: 6px;
                        padding: 14px;
                    }

                    .metric strong {
                        display: block;
                        font-size: 24px;
                        color: #0d5c75;
                    }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 28px;
                        background: #ffffff;
                    }

                    th, td {
                        border: 1px solid #d9e1ea;
                        padding: 8px 10px;
                        text-align: left;
                    }

                    th {
                        background: #e9f0f5;
                    }

                    .Pending {
                        color: #8a5a00;
                        font-weight: bold;
                    }

                    .Completed {
                        color: #0f6b3d;
                        font-weight: bold;
                    }

                    .Cancelled {
                        color: #9b1c31;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <h1>Healthcare Appointment Report</h1>

                <div class="summary">
                    <div class="metric">
                        <span>Total Clinics</span>
                        <strong><xsl:value-of select="count(/h:appointmentSystem/h:clinics/h:clinic)"/></strong>
                    </div>
                    <div class="metric">
                        <span>Total Doctors</span>
                        <strong><xsl:value-of select="count(/h:appointmentSystem/h:clinics/h:clinic/h:doctors/h:doctor)"/></strong>
                    </div>
                    <div class="metric">
                        <span>Total Patients</span>
                        <strong><xsl:value-of select="count(/h:appointmentSystem/h:patients/h:patient)"/></strong>
                    </div>
                    <div class="metric">
                        <span>Total Appointments</span>
                        <strong><xsl:value-of select="count(/h:appointmentSystem/h:appointments/h:appointment)"/></strong>
                    </div>
                </div>

                <h2>Clinics and Doctors</h2>
                <table>
                    <tr>
                        <th>Clinic ID</th>
                        <th>Clinic Name</th>
                        <th>Doctor ID</th>
                        <th>Doctor Name</th>
                        <th>Email</th>
                    </tr>
                    <xsl:for-each select="/h:appointmentSystem/h:clinics/h:clinic">
                        <xsl:variable name="clinicId" select="h:clinicId"/>
                        <xsl:variable name="clinicName" select="h:clinicName"/>
                        <xsl:for-each select="h:doctors/h:doctor">
                            <tr>
                                <td><xsl:value-of select="$clinicId"/></td>
                                <td><xsl:value-of select="$clinicName"/></td>
                                <td><xsl:value-of select="h:doctorId"/></td>
                                <td><xsl:value-of select="concat(h:firstName, ' ', h:lastName)"/></td>
                                <td><xsl:value-of select="h:email"/></td>
                            </tr>
                        </xsl:for-each>
                    </xsl:for-each>
                </table>

                <h2>Appointments</h2>
                <table>
                    <tr>
                        <th>Appointment ID</th>
                        <th>Date and Time</th>
                        <th>Patient</th>
                        <th>Doctor</th>
                        <th>Status</th>
                        <th>Notes</th>
                    </tr>
                    <xsl:for-each select="/h:appointmentSystem/h:appointments/h:appointment">
                        <xsl:sort select="h:appointmentDateTime"/>
                        <xsl:variable name="patientId" select="h:patientId"/>
                        <xsl:variable name="doctorId" select="h:doctorId"/>
                        <tr>
                            <td><xsl:value-of select="h:appointmentId"/></td>
                            <td><xsl:value-of select="h:appointmentDateTime"/></td>
                            <td>
                                <xsl:value-of select="/h:appointmentSystem/h:patients/h:patient[h:patientId=$patientId]/h:firstName"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="/h:appointmentSystem/h:patients/h:patient[h:patientId=$patientId]/h:lastName"/>
                                <xsl:text> (</xsl:text>
                                <xsl:value-of select="$patientId"/>
                                <xsl:text>)</xsl:text>
                            </td>
                            <td>
                                <xsl:value-of select="/h:appointmentSystem/h:clinics/h:clinic/h:doctors/h:doctor[h:doctorId=$doctorId]/h:firstName"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="/h:appointmentSystem/h:clinics/h:clinic/h:doctors/h:doctor[h:doctorId=$doctorId]/h:lastName"/>
                                <xsl:text> (</xsl:text>
                                <xsl:value-of select="$doctorId"/>
                                <xsl:text>)</xsl:text>
                            </td>
                            <td>
                                <span class="{h:status}">
                                    <xsl:value-of select="h:status"/>
                                </span>
                            </td>
                            <td><xsl:value-of select="h:notes"/></td>
                        </tr>
                    </xsl:for-each>
                </table>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
