azcopy login --service-principal --tenant-id $1 --application-id $2
storage_account=$3
operation=$4
if [ "$operation" == "pull" ]
then
    azcopy sync "https://$storage_account.blob.core.windows.net/config" "../automation-config" --exclude-pattern="*.log;*.sh;*.bak"
elif [ "$operation" == "push" ]
then
    azcopy sync "../automation-config" "https://$storage_account.blob.core.windows.net/config" --exclude-pattern="*.log;*.sh;*.bak"
fi