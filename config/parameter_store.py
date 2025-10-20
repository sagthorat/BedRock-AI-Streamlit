import boto3
import os
import logging
from botocore.exceptions import ClientError
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ParameterStoreConfig:
    def __init__(self, region: str = None):
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self._cache = {}
    
    def get_parameter(self, parameter_name: str, decrypt: bool = True) -> Optional[str]:
        """Get a single parameter from Parameter Store"""
        try:
            if parameter_name in self._cache:
                return self._cache[parameter_name]
            
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            self._cache[parameter_name] = value
            return value
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter {parameter_name} not found in Parameter Store")
                return None
            else:
                logger.error(f"Error retrieving parameter {parameter_name}: {e}")
                raise
    
    def get_parameters_by_path(self, path: str, decrypt: bool = True) -> Dict[str, str]:
        """Get multiple parameters by path prefix"""
        try:
            parameters = {}
            paginator = self.ssm_client.get_paginator('get_parameters_by_path')
            
            for page in paginator.paginate(
                Path=path,
                Recursive=True,
                WithDecryption=decrypt
            ):
                for param in page['Parameters']:
                    # Remove path prefix from parameter name
                    key = param['Name'].replace(path, '').lstrip('/')
                    parameters[key] = param['Value']
                    self._cache[param['Name']] = param['Value']
            
            return parameters
            
        except ClientError as e:
            logger.error(f"Error retrieving parameters by path {path}: {e}")
            raise

def get_app_config() -> Dict[str, str]:
    """Get application configuration from Parameter Store"""
    config = ParameterStoreConfig()
    app_path = "/bedrock-ai-app"
    
    # Try to get parameters from Parameter Store first
    try:
        params = config.get_parameters_by_path(app_path)
        if params:
            logger.info("Configuration loaded from Parameter Store")
            return {
                'agent_id': params.get('agent-id'),
                'agent_alias_id': params.get('agent-alias-id'),
                'ui_title': params.get('ui-title', 'AI-Powered Assistant'),
                'ui_icon': params.get('ui-icon', '🤖'),
                'aws_region': params.get('aws-region', 'us-east-1')
            }
    except Exception as e:
        logger.warning(f"Failed to load from Parameter Store: {e}")
    
    # Fallback to environment variables
    logger.info("Falling back to environment variables")
    return {
        'agent_id': os.getenv('BEDROCK_AGENT_ID'),
        'agent_alias_id': os.getenv('BEDROCK_AGENT_ALIAS_ID'),
        'ui_title': os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', 'AI-Powered Assistant'),
        'ui_icon': os.getenv('BEDROCK_AGENT_TEST_UI_ICON', '🤖'),
        'aws_region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    }