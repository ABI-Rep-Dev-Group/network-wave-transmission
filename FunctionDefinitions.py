#!/usr/bin/python
import numpy as np
import VesselDefinition as params
import matplotlib.pyplot as plt
##Function definitions: contains all the routines required to calculate admittance, sum through a network structure, apply boundary conditions and export solutions.
def total_resistance(vessels,terminals):
    #Calculates total resistance of the uterine arteries, outputs this resistance and a venous equivalent resistance (half of arterial resistance)
    resistance=np.zeros(np.size(vessels))
    flow = np.zeros(np.size(vessels)+1)
    total_resistance=0.0
    static_inlet_pressure = params.StaticPressure #Units of Pascals
    static_inlet_flow = params.SteadyFlow*1000./60. #ml/min converted to mm^3/s
    pressure_out = np.zeros(np.size(vessels)+1)

    print("=====================================")
    print("Flow and Pressure in each vessel type")
    print("=====================================")
    anast_index = 0 #initialise
    for i in range(0,np.size(vessels)):
        # Poiseille resistance of each vessels
        # Units of resistance are Pa.s/mm^3
        resistance[i]=81.0*params.mu*vessels['length'][i]/(8.0*np.pi* vessels['radius'][i]**4.0)/vessels['number'][i]

        print(vessels['vessel_type'][i], resistance[i])

        if(vessels['vessel_type'][i]=='Anastomose'):
            anast_index=i
        else:
            if i == 0:
                flow[i]=static_inlet_flow/vessels['number'][i] #Assuming all arteries of a specific level are the same we just divide the flow
                pressure_out[i] = static_inlet_pressure-resistance[i]*flow[i]
            else:
                flow[i]=flow[i-1]*vessels['number'][i-1]/vessels['number'][i]
                pressure_out[i] = pressure_out[i-1] - resistance[i] * static_inlet_flow

            total_resistance=total_resistance+resistance[i]
            print(str(vessels['vessel_type'][i]) + ' flow: ' + str(flow[i]) + ' mm^3/s ' + str(
                flow[i] * 60. / 1000.) + ' ml/min ' + str(flow[i] * 60.) + ' ul/min ')
            print(str(vessels['vessel_type'][i]) + ' pressure out: ' + str(pressure_out[i]) + ' Pa ' + str(
                pressure_out[i] / 133.) + ' mmHg ')

    if(vessels['length'][anast_index]==0.0) or (anast_index == 0):
        venous_resistance=0.0
        #Only IVS contribution to resistance (as in Mo et al. A transmission line modelling approach to the interpretation of uterine doppler waveforms. Ultrasound in Medicine and Biology, 1988. 14(5): p. 365-376.)
        parallel_resistance=terminals[0] #Pa.s/mm^3
        flow[np.size(vessels)] = flow[np.size(vessels)-2]
        pressure_out[np.size(vessels)] = pressure_out[np.size(vessels)-2] - parallel_resistance * flow[np.size(vessels)]*vessels['number'][np.size(vessels)-2]

        print('Terminal  flow: ' + str(flow[np.size(vessels)]) + ' mm^3/s ' + str(
            flow[np.size(vessels)] * 60. / 1000.) + ' ml/min ' + str(flow[np.size(vessels)] * 60.) + ' ul/min ')
        print('Terminal pressure out: ' + str(pressure_out[np.size(vessels)]) + ' Pa ' + str(
            pressure_out[np.size(vessels)] / 133.) + ' mmHg ')
    else:        
        venous_resistance=total_resistance/2.0 #Assuming veins are half as resistive as arteries
        #add terminal and anastomosis resistance in parallel
        flow[anast_index]=(1.-(resistance[anast_index]+venous_resistance)/(resistance[anast_index]+venous_resistance+terminals[2]*terminals[0]))*flow[np.size(vessels) - 2]
        flow[np.size(vessels)]=flow[np.size(vessels)-2]-flow[anast_index]
        parallel_resistance=1.0/(1.0/(resistance[anast_index]+venous_resistance)+terminals[2]*1.0/terminals[0])

        pressure_out[np.size(vessels)] = pressure_out[np.size(vessels)-2] - terminals[2]*terminals[0] * flow[np.size(vessels)]*vessels['number'][np.size(vessels)-2]
        pressure_out[anast_index] = pressure_out[np.size(vessels) - 2] - (resistance[anast_index]+venous_resistance) * flow[anast_index]*vessels['number'][anast_index]
        print('Anastomosis flow: ' + str(flow[anast_index]) + ' mm^3/s ' + str(
            flow[anast_index] * 60. / 1000.) + ' ml/min ' + str(flow[anast_index] * 60.) + ' ul/min ')
        print('Anastomosis pressure out: ' + str(pressure_out[anast_index]) + ' Pa ' + str(
            pressure_out[anast_index] / 133.) + ' mmHg ')
        print('Terminal  flow: ' + str(flow[np.size(vessels)]) + ' mm^3/s ' + str(
            flow[np.size(vessels)] * 60. / 1000.) + ' ml/min ' + str(flow[np.size(vessels)] * 60.) + ' ul/min ')
        print('Terminal pressure out: ' + str(pressure_out[np.size(vessels)]) + ' Pa ' + str(
            pressure_out[np.size(vessels)] / 133.) + ' mmHg ')
    total_resistance=total_resistance+parallel_resistance


    print("===============")
    print("Shear Stresses")
    print("===============")
    shear = np.zeros(np.size(vessels))
    for i in range(0, np.size(vessels)):
        shear[i] = 4. * params.mu * flow[i] / (np.pi * vessels['radius'][i]**3.)
        print(str(vessels['vessel_type'][i]) + ' shear: ' + str(shear[i]) + ' Pa ' + str(shear[i]/10) + ' dyne/cm3')

    print("================")
    print("Total Resistance")
    print("================")
    print(str(total_resistance) + "Pa.mm^3/s")
    print("=============================")
    print("Total estimated pressure drop")
    print("=============================")
    print(str(total_resistance*static_inlet_flow) + " Pa, " + str(total_resistance*static_inlet_flow/133.) + " mmHg")

    return [total_resistance,venous_resistance]
    
    
def characteristic_admittance(vessels,terminals):
    #Calculates characteristic admittance of each blood vessel following the model employed by Mo et al. A transmission line modelling approach to the interpretation of uterine doppler waveforms. Ultrasound in Medicine and Biology, 1988. 14(5): p. 365-376. Outputs characteristic admittance, propagation constant and uterine artery compliance
    #initialise admitance and propogation constant
    char_admit=np.zeros((np.size(vessels),params.NHar),dtype=complex)
    prop_const=np.zeros((np.size(vessels),params.NHar),dtype=complex)
    C=np.zeros(np.size(vessels))
    L=np.zeros(np.size(vessels))
    R=np.zeros(np.size(vessels))
    G=np.zeros(np.size(vessels))
    for i in range(0,np.size(vessels)):
        hbar=params.h*vessels['radius'][i]
        C[i]=3.0*np.pi*vessels['radius'][i]**3/(2.0*hbar*params.E)# Compliance per unit length mm^3/Pa
        L[i]=9.0*params.rho/(4.0*np.pi*vessels['radius'][i]**2)#inertia term per unit length g/mm5
        R[i]=81.0*params.mu/(8.0*np.pi*vessels['radius'][i]**4) #laminar resistance per unit length Pa.s/mm4
        G[i]=0.0
        for j in range(0,params.NHar):
            omega=(j+1)*2.0*np.pi*params.HeartRate/60.0
            char_admit[i][j]=np.sqrt(G[i]+np.complex(0.0,1.0)*omega*C[i])/np.sqrt(R[i]+np.complex(0.0,1.0)*omega*L[i])*vessels['number'][i] #summed in parallel
            prop_const[i][j]=np.sqrt((G[i]+np.complex(0.0,1.0)*omega*C[i])*(R[i]+np.complex(0.0,1.0)*omega*L[i]))
            
    utcomp=C[0]
    return [char_admit,prop_const,utcomp]
    
def effective_admittance(vessels,terminals,char_admit,prop_const,v_resist):
    #Calculates effective  admittance and reflection coefficient of each of each blood vessel. Outputs are effective admittance and reflection coefficient
    #initialise effective admittance and reflection coefficiet
    eff_admit=np.zeros((np.size(vessels),params.NHar),dtype=complex)
    reflect=np.zeros((np.size(vessels),params.NHar),dtype=complex)
    #First consider the terminal admitance, which is the admittance of the asastomoses and veins (in series) added in parallel to the SA/IVS admittance
    for i in range(0,np.size(vessels)):
        if(vessels['vessel_type'][i]=='Anastomose'):
            for j in range(0,params.NHar):
                eff_admit[i][j]=char_admit[i][j]/(1.0+char_admit[i][j]*v_resist) #adding venous resistance in series
            for j in range(0,params.NHar):
                omega=(j+1)*2.0*np.pi*params.HeartRate/60.0
                IVS_admit=terminals[2]*(1.0+np.complex(0.0,1.0)*omega*terminals[0]*terminals[1])/terminals[0]
                eff_admit[i][j]=eff_admit[i][j]+IVS_admit
                
    #Step backward through network and calculate effecitive admittances 
    for i in range(np.size(vessels)-2,-1,-1):
        daughter_admit=eff_admit[i+1][:]
        reflect[i][:]=np.divide(char_admit[i][:]-daughter_admit,char_admit[i][:]+daughter_admit)
        eff_admit[i][:]=char_admit[i][:]*(1.0-reflect[i][:]*np.exp(-2.0*prop_const[i][:]*vessels['length'][i]))\
            /(1.0+reflect[i][:]*np.exp(-2.0*prop_const[i][:]*vessels['length'][i]))
    #print(reflect)
    return [eff_admit,reflect]


def flow_factor(vessels,terminals,char_admit,prop_constant,reflect_coeff):
    #calculates how flow propagates through the tree
    #print(prop_constant)
    q_factor = np.zeros((np.size(vessels), params.NHar), dtype=complex)
    for i in range(0,np.size(vessels)):
            upstream_element = vessels['generation'][i]-2 #could be generalised to search for generation above
            #print(i,upstream_element)
            for j in range(0,params.NHar):
                omega=(j+1)*2.0*np.pi*params.HeartRate/60.0
                if (upstream_element == -1):
                    q_factor[i][j] = 1.0

                else:
                    q_factor[i][j] =  q_factor[upstream_element][j]*(1.+reflect_coeff[upstream_element][j]) * \
                                      np.exp(-1. * vessels['length'][upstream_element]*prop_constant[upstream_element][j]) \
                                      / (char_admit[upstream_element][j]*(1+reflect_coeff[i][j])*np.exp(-2.* \
                                      vessels['length'][i]*prop_constant[i][j]))
    return q_factor
    
def flow_velocity_properties(velocity):
    #Outputs properties of the velocity waveform
    print("Velocity waveform properties ")
    print("=============================")
    print('S/D = ' + str(np.max(velocity)/np.min(velocity)))
    print('RI = ' + str((np.max(velocity)-np.min(velocity))/np.max(velocity)))
    print('PI = ' + str((np.max(velocity)-np.min(velocity))*np.size(velocity)/np.sum(velocity)))
    
    #check for notch - note that this is a simple assessment of the characteristics of the waveform and will fail fo some complicated waveforms but works for most physiologically realistic parameter sets. Plot your waveform if you are simulating something perturbed far from the phyisological range (especially with many reflections) to confirm accuracy of outputs.
    point1=1
    point2=1
    checksize=np.size(velocity)-2
    while(velocity[point1+1]>velocity[point1] and point1<checksize): #expect one monotonically increasing then decreasing waveform prior to notch
        point1=point1+1
    while(velocity[point1+1]<velocity[point1] and point1<checksize):
        point1=point1+1
    point2=point1
    while(velocity[point2+1]>velocity[point2] and point2<checksize):
        point2=point2+1
    if(point1 < point2):
        print("Notch present")
        print("Notch height " + str(velocity[point2]-velocity[point1]))
        print("Notch ratio "+ str((velocity[point2]-velocity[point1])/(np.max(velocity)-np.min(velocity))))
        
    else:
        print("No notch present")



        
def timecourse(StartTime,EndTime,dt,reflect_coeff,char_admit,wave_prop_constant,SteadyFlow,UtCompliance,vessel):
    #Convert admittance spectra to time dependent waveforms as described by Mo et al. A transmission line modelling approach to the interpretation of uterine doppler waveforms. Ultrasound in Medicine and Biology, 1988. 14(5): p. 365-376.) Output is insonation site velocity and time, for plotting but interested users can add outputs.
    print(vessel)
    for i in range(0, np.size(params.vessels)):
        if(params.vessels['vessel_type'][i]==vessel):
            vessel_index = i

    LengthOfUterine=params.vessels['length'][vessel_index] #mm
    UterineRadius=params.vessels['radius'][vessel_index]#mm
    if(vessel == 'Uterine'):
        assemssment_point = params.Dist2Inson

    #define time coursr
    NTime=int(np.ceil((EndTime-StartTime)/dt))
    time=np.zeros(NTime)
    IncidentFlow=np.zeros(NTime)
    #initialise waveforms
    InsonationIncidentFlow=np.zeros(NTime) #ml/min
    InsonationReflectFlow=np.zeros(NTime) #ml/min
    InsonationSitePressureIn=np.zeros(NTime) #Pa
    InsonationSitePressureRef=np.zeros(NTime) #Pa
    InsonationSitePressure=np.zeros(NTime) #Pa
    InsonationSiteVelocity=np.zeros(NTime) #cm/s
    InsonationSiteTotalFlow=np.zeros(NTime)
    for i in range(0,NTime):
        time[i]=dt*i
        for j in range(0,params.NHar):

            IncidentFlow[i]=IncidentFlow[i]+params.IWavHar[1,j]*np.cos(2*np.pi*time[i]*params.IWavHar[0,j]+params.IWavHar[2,j])
        
            InsonationIncidentFlow[i]=InsonationIncidentFlow[i]+\
            params.IWavHar[1,j]*np.exp(-assemssment_point*wave_prop_constant[0,j])*\
            np.cos(2*np.pi*time[i]*params.IWavHar[0,j]+params.IWavHar[2,j]-wave_prop_constant[1,j]*assemssment_point)
        
            InsonationReflectFlow[i]=InsonationReflectFlow[i]-\
            reflect_coeff[0,j]*params.IWavHar[1,j]*np.exp((-assemssment_point-LengthOfUterine)*wave_prop_constant[0,j])*\
            np.cos(2*np.pi*time[i]*params.IWavHar[0,j]+params.IWavHar[2,j]-wave_prop_constant[1,j]*(assemssment_point+LengthOfUterine)+reflect_coeff[1,j])
        
            #Incident pressure is characteristic impedance times incident flow
            InsonationSitePressureIn[i]=InsonationSitePressureIn[i]+\
                    params.IWavHar[1,j]*np.exp(-assemssment_point*wave_prop_constant[0,j])*1000.0/60.0*\
                    np.cos(2*np.pi*time[i]*params.IWavHar[0,j]+params.IWavHar[2,j]-wave_prop_constant[1,j]*assemssment_point-char_admit[1,j])/char_admit[0,j]
        
            #Reflected pressure is characteristic impedance times reflcted flow
            InsonationSitePressureRef[i]=InsonationSitePressureRef[i]+\
            reflect_coeff[0,j]*params.IWavHar[1,j]*np.exp((-assemssment_point-LengthOfUterine)*wave_prop_constant[0,j])*1000.0/60.0*\
            np.cos(2*np.pi*time[i]*params.IWavHar[0,j]+params.IWavHar[2,j]-wave_prop_constant[1,j]*(assemssment_point+LengthOfUterine)+reflect_coeff[1,j]-char_admit[1,j])/char_admit[0,j]
        
                
            InsonationSitePressure[i]=InsonationSitePressureIn[i]+InsonationSitePressureRef[i]+params.StaticPressure
            InsonationSiteTotalFlow[i]= InsonationIncidentFlow[i]+InsonationReflectFlow[i]+SteadyFlow
            InsonationSiteVelocity[i]=(InsonationSiteTotalFlow[i])*(1000.0/60.0)/(np.pi*UterineRadius*UterineRadius+UtCompliance*(InsonationSitePressure[i]))/10.0
    
    return [InsonationSiteVelocity,InsonationSiteTotalFlow, InsonationSitePressure,time]

def any_timecourse(StartTime,EndTime,dt,q_factor,char_admit):
    vessel = 'Radial'
    for i in range(0, np.size(params.vessels)):
        if(params.vessels['vessel_type'][i]==vessel):
            vessel_index = i

    #define time course
    NTime=int(np.ceil((EndTime-StartTime)/dt))
    time=np.zeros(NTime)
    print(vessel_index)
    forward_pressure = np.zeros(NTime)  # Pa
    for i in range(0,NTime):
        time[i]=dt*i
        for j in range(0,params.NHar):
            forward_pressure[i] = forward_pressure[i] + abs(q_factor[vessel_index][j])/abs(char_admit[vessel_index][j])




    plt.plot(forward_pressure)
    plt.show()
