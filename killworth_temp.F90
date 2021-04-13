      !=====================================================================!
      !         This program performs time interpolation on the basis       !
      !         of Killworth, 1996                                          !
      !                                                                     !
      !  D. Delrosso, 24th November 2016                                    !
      !=====================================================================!


      PROGRAM killworth_time_interpolation
      USE netcdf
      IMPLICIT NONE

!     DECLARATION SECTION 
      CHARACTER (len = 100)     :: argclim          ! climatology .txt to read (argument)     
      REAL, DIMENSION(1,12)     :: climrvr          ! climatological values series
      REAL, DIMENSION(1,14)     :: extclimrvr       ! climatological values extended series     
      INTEGER                   :: k                ! loop indexes
      INTEGER                   :: i, j, z          ! loop indexes
      INTEGER, DIMENSION(1,16)  :: l                ! number of days in each month 
      REAL, DIMENSION(1,14)     :: e, g, f          ! matrix coefficients
      REAL, DIMENSION(14,14)    :: A                ! matrix
      REAL, DIMENSION(14,14)    :: AA               ! inverse matrix of A
      REAL, DIMENSION(14,14)    :: UNI
      REAL, DIMENSION(1,14)     :: pseudodischarge  ! pseudodischarge matrix      
      REAL                      :: l1, lm1, lp1
      INTEGER                   :: nx, ny           ! dimensions of matrix A
!     FINDInv subroutine section
      REAL, ALLOCATABLE, DIMENSION(:,:) :: Matrix, invMatrix
      INTEGER                           :: n, ErrorFlag
!     interp1 subroutine section
      REAL, ALLOCATABLE, DIMENSION(:,:) :: xData, yData,xd,yd
      REAL, ALLOCATABLE, DIMENSION(:,:) :: xVal
      INTEGER                           :: ikm, okm,nd,ni
      REAL, ALLOCATABLE, DIMENSION(:,:) :: yVal,yi
      INTEGER                           :: inputIndex, dataIndex
      REAL, ALLOCATABLE, DIMENSION(:,:) :: weight
      REAL                              :: minXdata, minYdata, xRange
!     linear interpolation section
      INTEGER, DIMENSION(1,14)              :: timein,timeintotimeout          ! Array from [1:14] number
      INTEGER                               :: it, ot          ! Loop indexes
      INTEGER                               :: countertime,counterdays     ! Time counter

!     EXECUTION SECTION

!     Read input file
      CALL getarg(1, argclim)

      OPEN(10,file=argclim,status='old')
      READ(10,*) climrvr
      CLOSE(10)


!     Extend climatological series for ensure cyclicity
      DO k=1,12
        extclimrvr(1,k+1) = climrvr(1,k)
      END DO

      extclimrvr(1,1)     = climrvr(1,12)
      extclimrvr(1,14)    = climrvr(1,1)        


!     General formulation for getting daily values from monthly values
!     b = A * d  where b are daily values, A is a tridiagonal matrix 
!     and d are climatological values      
      j = 1
      l = RESHAPE((/ %NOV_TO_FEB_NUM_OF_DAYS% /), SHAPE(l)) 
      ! november to february number of days

      DO i = 2,15
        l1 = l(1,i)
        lm1= l(1,i-1)
        lp1= l(1,i+1)        
        e(1,j)= l1 / ( 4 * (lm1 + l1) )    
        g(1,j)= l1 / ( 4 * (l1  + lp1))
        f(1,j)= 1  - e(1,j) - g(1,j)
        j=j+1        

      END DO     


!     Matrix A definition
      A(1,:)  = (/ f(1,1),g(1,1),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,1) /)
      A(2,:)  = (/ e(1,2),f(1,2),g(1,2),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(3,:)  = (/ 0.0,e(1,3),f(1,3),g(1,3),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(4,:) = (/ 0.0,0.0,e(1,4),f(1,4),g(1,4),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(5,:) = (/ 0.0,0.0,0.0,e(1,5),f(1,5),g(1,5),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(6,:) = (/ 0.0,0.0,0.0,0.0,e(1,6),f(1,6),g(1,6),0.0,0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(7,:) = (/ 0.0,0.0,0.0,0.0,0.0,e(1,7),f(1,7),g(1,7),0.0,0.0,0.0,0.0,0.0,0.0 /)
      A(8,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,e(1,8),f(1,8),g(1,8),0.0,0.0,0.0,0.0,0.0 /)
      A(9,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,9),f(1,9),g(1,9),0.0,0.0,0.0,0.0 /)
      A(10,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,10),f(1,10),g(1,10),0.0,0.0,0.0 /)
      A(11,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,11),f(1,11),g(1,11),0.0,0.0 /)
      A(12,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,12),f(1,12),g(1,12),0.0 /)
      A(13,:) = (/ 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,13),f(1,13),g(1,13) /)
      A(14,:) = (/ g(1,14),0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,e(1,14),f(1,14) /)

      
      nx = SIZE(A(1,:))
      ny = SIZE(A(:,1))

!     Compute AA inverse matrix of A
      CALL FindInv(A,AA,nx,ErrorFlag)

!     Compute pseudodischarge d' = AA * d
      CALL MULT(pseudodischarge,extclimrvr,AA,nx,nx,nx)

      ! Create arrays for time interpolation
      countertime = 1
      counterdays = 0
      DO it = 1,14
        timein(1,it) = countertime
        countertime  = countertime +1
        IF ( it == 1) THEN
           timeintotimeout(1,it)=FLOOR(l(1,it)/2.0)
        ELSE
           timeintotimeout(1,it)=counterdays+FLOOR(l(1,it)/2.0)
        END IF
        counterdays = counterdays + l(1,it)
      END DO 
 
      ! Print pseudoscharge in the middle of the current month
      DO it = 1,14
         PRINT*,timeintotimeout(1,it),pseudodischarge(1,it)
      END DO


      END PROGRAM killworth_time_interpolation


        !Subroutine to find the inverse of a square matrix
        !Author : Louisda16th a.k.a Ashwith J. Rego
        !Reference : Algorithm has been well explained in:
        !http://math.uww.edu/~mcfarlat/inverse.htm           
        !http://www.tutor.ms.unimelb.edu.au/matrix/matrix_inverse.html

        SUBROUTINE FINDInv(matrix, inverse, n, errorflag)
        IMPLICIT NONE
        !Declarations
        INTEGER, INTENT(IN) :: n
        INTEGER, INTENT(OUT) :: errorflag  !Return error status. -1 for error, 0 for normal
        REAL, INTENT(IN), DIMENSION(n,n) :: matrix  !Input matrix
        REAL, INTENT(OUT), DIMENSION(n,n) :: inverse !Inverted matrix
        
        LOGICAL :: FLAG = .TRUE.
        INTEGER :: i, j, k, l
        REAL :: m
        REAL, DIMENSION(n,2*n) :: augmatrix !augmented matrix
        
        !Augment input matrix with an identity matrix
        DO i = 1, n
                DO j = 1, 2*n
                        IF (j <= n ) THEN
                                augmatrix(i,j) = matrix(i,j)
                        ELSE IF ((i+n) == j) THEN
                                augmatrix(i,j) = 1
                        Else
                                augmatrix(i,j) = 0
                        ENDIF
                END DO
        END DO
        
        !Reduce augmented matrix to upper traingular form
        DO k =1, n-1
                IF (augmatrix(k,k) == 0) THEN
                        FLAG = .FALSE.
                        DO i = k+1, n
                                IF (augmatrix(i,k) /= 0) THEN
                                        DO j = 1,2*n
                                                augmatrix(k,j) = augmatrix(k,j)+augmatrix(i,j)
                                        END DO
                                        FLAG = .TRUE.
                                        EXIT
                                ENDIF
                                IF (FLAG .EQV. .FALSE.) THEN
                                        PRINT*, "Matrix non-invertible"
                                        inverse = 0
                                        errorflag = -1
                                        return
                                ENDIF
                        END DO
                ENDIF
                DO j = k+1, n                   
                        m = augmatrix(j,k)/augmatrix(k,k)
                        DO i = k, 2*n
                                augmatrix(j,i) = augmatrix(j,i) - m*augmatrix(k,i)
                        END DO
                END DO
        END DO
        
        !Test for invertibility
        DO i = 1, n
                IF (augmatrix(i,i) == 0) THEN
                        PRINT*, "Matrix is non - invertible"
                        inverse = 0
                        errorflag = -1
                        return
                ENDIF
        END DO
        
        !Make diagonal elements as 1
        DO i = 1 , n
                m = augmatrix(i,i)
                DO j = i , (2 * n)                              
                           augmatrix(i,j) = (augmatrix(i,j) / m)
                END DO
        END DO
        
        !Reduced right side half of augmented matrix to identity matrix
        DO k = n-1, 1, -1
                DO i =1, k
                m = augmatrix(i,k+1)
                        DO j = k, (2*n)
                                augmatrix(i,j) = augmatrix(i,j) -augmatrix(k+1,j) * m
                        END DO
                END DO
        END DO                          
        
        !store answer
        DO i =1, n
                DO j = 1, n
                        inverse(i,j) = augmatrix(i,j+n)
                END DO
        END DO
        errorflag = 0
        END SUBROUTINE FINDinv

        SUBROUTINE MULT(Y,X,A,LA,M,N)
!     |________________________________________________________|
!     |       MULTIPLY A GENERAL REAL MATRIX BY A VECTOR       |
!     |                                                        |
!     |    INPUT:                                              |
!     |                                                        |
!     |         X     --VECTOR                                 |
!     |                                                        |
!     |         A     --ARRAY CONTAINING COEFFICIENT MATRIX    |
!     |                                                        |
!     |         LA    --LEADING (ROW) DIMENSION OF ARRAY A     |
!     |                                                        |
!     |         M     --NUMBER OF ROWS IN COEFFICIENT MATRIX   |
!     |                                                        |
!     |         N     --NUMBER OF COLUMNS IN COEFF. MATRIX     |
!     |                                                        |
!     |    OUTPUT:                                             |
!     |                                                        |
!     |         Y     --PRODUCT BETWEEN A AND X                |
!     |________________________________________________________|
!
      INTEGER I,J,M,N,LA
      REAL A(LA,1),X(1),Y(1),T
      DO 10 I = 1,M
10         Y(I) = 0.
      DO 20 J = 1,N
           T = X(J)
           DO 30 I = 1,M
              Y(I) = Y(I) + A(I,J)*T
 30        continue
 20   continue
      RETURN
      END SUBROUTINE MULT

