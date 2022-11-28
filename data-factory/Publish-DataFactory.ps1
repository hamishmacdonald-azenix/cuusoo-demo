param (
  [Parameter(Mandatory)][string]$ClientID
  , [Parameter(Mandatory)][string]$ClientSecret
  , [Parameter(Mandatory)][string]$TenantID
  , [Parameter(Mandatory)][string]$SubscriptionID
  , [Parameter(Mandatory)][string]$Location
  , [Parameter(Mandatory)][string]$ResourceGroupName
  , [Parameter(Mandatory)][string]$DataFactoryName
  , [Parameter(Mandatory)][string]$Environment
)

#Removing installation
# Import-Module Az.Accounts, Az.DataFactory, Az.Resources, azure.datafactory.tools
# Install the required modules
$requiredModules = @("Az.Accounts", "Az.DataFactory", "Az.Resources", "azure.datafactory.tools")
$installedModules = Get-InstalledModule

foreach ($module in $requiredModules) {
  if (!($installedModules | Where-Object { $_.Name -eq $module })) {
    Write-Output "Installing $module module"
    Install-Module $module -AllowClobber -Force
  }
}

# Connect to Azure


$ClientSecretSecure = ConvertTo-SecureString $ClientSecret -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential $ClientID, $ClientSecretSecure

Connect-AzAccount -ServicePrincipal `
  -Tenant $TenantID `
  -Credential $credential `
  -Subscription $SubscriptionID

$existingDataFactoryResource = Get-AzDataFactoryV2 -ResourceGroupName $ResourceGroupName -Name $DataFactoryName -ErrorAction SilentlyContinue
if ($null -eq $existingDataFactoryResource) {
  throw 'Unable to find an existing DataFactory resource named ''{0}'' in resource group ''{1}''' -f $DataFactoryName, $ResourceGroupName
}

$publishDataFactoryOptions = New-AdfPublishOption
$publishDataFactoryOptions.CreateNewInstance = $false
$publishDataFactoryOptions.DeleteNotInSource = $true
$publishDataFactoryOptions.DeployGlobalParams = $false

$dataFactoryLocation = $PSScriptRoot + "/"

$publishDataFactoryParams = @{
  RootFolder        = $dataFactoryLocation
  ResourceGroupName = $ResourceGroupName
  DataFactoryName   = $DataFactoryName
  Location          = $Location
  Stage             = $Environment
  Option            = $publishDataFactoryOptions
}

Publish-AdfV2FromJson @publishDataFactoryParams
